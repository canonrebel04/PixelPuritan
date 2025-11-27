import io
from fastapi.testclient import TestClient
from server.main import app
from PIL import Image


def test_rate_limit_429(monkeypatch):
    # Tighten limits to force 429
    monkeypatch.setenv("PIXELPURITAN_RATE_LIMIT_RPS", "1")
    monkeypatch.setenv("PIXELPURITAN_RATE_LIMIT_BURST", "2")
    client = TestClient(app)

    # Generate a valid tiny PNG to avoid PIL decode errors
    img = Image.new('RGB', (8, 8), (10, 20, 30))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    png_bytes = buf.getvalue()
    files = {"file": ("x.png", png_bytes, "image/png")}
    # First two should pass, subsequent should hit 429
    r1 = client.post("/v1/detect", files=files)
    r2 = client.post("/v1/detect", files=files)
    r3 = client.post("/v1/detect", files=files)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 429
