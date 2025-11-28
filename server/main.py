from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from PIL import Image
import io
import logging
from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import os
import uuid
import time
import configparser

app = FastAPI(title="PixelPuritan AI Server")

# Logging Setup
logger = logging.getLogger("pixelpuritan")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.handlers = [handler]

# --- MODEL LOADING ---
# Using ViT Base NSFW Detector (Better accuracy than ResNet)
MODEL_NAME = "AdamCodd/vit-base-nsfw-detector"
logger.info(f"Loading Model: {MODEL_NAME}...")
device = -1

classifier = None
if os.getenv("PIXELPURITAN_DUMMY_MODEL") == "1":
    logger.info("Using dummy classifier for tests (PIXELPURITAN_DUMMY_MODEL=1)")
    def _dummy_classifier(image):
        # Return a stable output
        return [
            {"label": "safe", "score": 0.99},
            {"label": "nsfw", "score": 0.01},
        ]
    classifier = _dummy_classifier
else:
    try:
        # Lazy import heavy libs only when real model is needed
        from transformers import pipeline
        import torch
        device = 0 if torch.cuda.is_available() else -1
        logger.info(f"Using device: {'GPU' if device == 0 else 'CPU'}")
        classifier = pipeline("image-classification", model=MODEL_NAME, device=device)
        logger.info("✅ Model loaded successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        raise e

# Prometheus metrics
requests_total = Counter(
    "pp_requests_total",
    "Total detect requests",
    ["status"]
)
latency_seconds = Histogram(
    "pp_inference_latency_seconds",
    "Inference latency in seconds"
)

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Middleware to attach request id and structured logs
@app.middleware("http")
async def add_request_id_logging(request: Request, call_next):
    req_id = str(uuid.uuid4())
    request.state.req_id = req_id
    logger.info("request.start", extra={
        "event": "request.start",
        "req_id": req_id,
        "path": request.url.path,
        "method": request.method,
    })
    response = await call_next(request)
    logger.info("request.end", extra={
        "event": "request.end",
        "req_id": req_id,
        "status_code": response.status_code,
    })
    response.headers["X-Request-ID"] = req_id
    return response

def _load_server_config():
    cfg = configparser.ConfigParser()
    cfg.read([
        os.path.expanduser("~/.config/pixelpuritan/config.ini"),
        os.path.join(os.path.dirname(__file__), "../config/defaults.ini"),
    ])
    rate_rps = os.getenv("PIXELPURITAN_RATE_LIMIT_RPS") or cfg.get("server", "rate_limit_rps", fallback="5")
    rate_burst = os.getenv("PIXELPURITAN_RATE_LIMIT_BURST") or cfg.get("server", "rate_limit_burst", fallback="10")
    api_key = os.getenv("PIXELPURITAN_API_KEY") or cfg.get("server", "api_key", fallback=None)
    return float(rate_rps), int(rate_burst), api_key

# Simple per-IP rate limiting (in-memory token bucket)
RATE_LIMIT_RPS, BURST, CONFIG_API_KEY = _load_server_config()
_buckets = {}

def _allow(ip: str, now: float):
    bucket = _buckets.get(ip)
    if bucket is None:
        _buckets[ip] = {"tokens": BURST, "last": now}
        return True
    elapsed = now - bucket["last"]
    # refill tokens at RATE_LIMIT_RPS
    bucket["tokens"] = min(BURST, bucket["tokens"] + elapsed * RATE_LIMIT_RPS)
    bucket["last"] = now
    if bucket["tokens"] >= 1:
        bucket["tokens"] -= 1
        return True
    return False

@app.post("/v1/detect")
async def detect(request: Request, file: UploadFile = File(...)):
    # Refresh config each request to honor env changes (useful in tests)
    global RATE_LIMIT_RPS, BURST, CONFIG_API_KEY
    RATE_LIMIT_RPS, BURST, CONFIG_API_KEY = _load_server_config()
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not _allow(client_ip, time.time()):
        requests_total.labels(status="429").inc()
        raise HTTPException(status_code=429, detail="Too Many Requests")
    # Optional API key auth
    api_key_required = CONFIG_API_KEY
    if api_key_required:
        supplied = request.headers.get("X-API-Key")
        if supplied != api_key_required:
            requests_total.labels(status="401").inc()
            raise HTTPException(status_code=401, detail="Unauthorized")
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        # Basic validation: size limit (e.g., 20MB) and MIME
        contents = await file.read()
        if len(contents) > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 20MB)")
        # Read Image safely
        image = Image.open(io.BytesIO(contents))
        image.verify()  # validate integrity
        image = Image.open(io.BytesIO(contents)).convert('RGB')  # reopen after verify

        # Inference with latency measurement
        with latency_seconds.time():
            results = classifier(image)

        # Parse Results (Model returns list of dicts: [{'label': 'nsfw', 'score': 0.99}, ...])
        # We need to find the 'nsfw' score or determining label.
        # This specific model usually outputs labels: 'nsfw', 'normal' (or similar)

        # Logic for AdamCodd/vit-base-nsfw-detector
        # Labels are usually 'nsfw' and 'safe' (or 'normal')
        is_nsfw = False
        confidence = 0.0

        # Check all results to find NSFW score specifically
        nsfw_score = 0.0
        for res in results:
            if res['label'].lower() == 'nsfw':
                nsfw_score = res['score']

        # Threshold definition
        if nsfw_score > 0.5:
            is_nsfw = True
            confidence = round(nsfw_score * 100, 2)
        else:
            is_nsfw = False
            # Confidence is the inverse
            confidence = round((1.0 - nsfw_score) * 100, 2)

        resp = {
            "file_name": file.filename,
            "is_nsfw": is_nsfw,
            "confidence_percentage": confidence
        }
        requests_total.labels(status="200").inc()
        logger.info(
            "inference.success",
            extra={
                "event": "inference.success",
                "req_id": getattr(request.state, "req_id", None),
                "file_name": file.filename,
                "is_nsfw": is_nsfw,
                "confidence": confidence,
            },
        )
        return resp

    except HTTPException as he:
        # Preserve intended HTTP errors (e.g., 413, 401, 429)
        try:
            requests_total.labels(status=str(he.status_code)).inc()
        except Exception:
            pass
        raise
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        requests_total.labels(status="500").inc()
        raise HTTPException(status_code=500, detail="Internal Server Error")
