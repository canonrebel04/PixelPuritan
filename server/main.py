from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from transformers import pipeline
from PIL import Image
import io
import logging

app = FastAPI(title="PixelPuritan AI Server")

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- MODEL LOADING ---
# Using ViT Base NSFW Detector (Better accuracy than ResNet)
MODEL_NAME = "AdamCodd/vit-base-nsfw-detector"
logger.info(f"Loading Model: {MODEL_NAME}...")

try:
    classifier = pipeline("image-classification", model=MODEL_NAME)
    logger.info("✅ Model loaded successfully.")
except Exception as e:
    logger.error(f"❌ Failed to load model: {e}")
    raise e

@app.post("/v1/detect")
async def detect(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        # Read Image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # Inference
        results = classifier(image)

        # Parse Results (Model returns list of dicts: [{'label': 'nsfw', 'score': 0.99}, ...])
        # We need to find the 'nsfw' score or determining label.
        # This specific model usually outputs labels: 'nsfw', 'normal' (or similar)

        # Find best prediction
        top_result = max(results, key=lambda x: x['score'])

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

        return {
            "file_name": file.filename,
            "is_nsfw": is_nsfw,
            "confidence_percentage": confidence
        }

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))
