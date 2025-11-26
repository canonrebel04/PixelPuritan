import io
from PIL import Image
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

def make_image_bytes(width=64, height=64, color=(0, 0, 0)):
    img = Image.new('RGB', (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def test_detect_ok():
    img_bytes = make_image_bytes()
    files = {"file": ("test.png", img_bytes, "image/png")}
    resp = client.post("/v1/detect", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert "is_nsfw" in data
    assert "confidence_percentage" in data

def test_detect_too_large():
    # 21MB payload
    big = b"0" * (21 * 1024 * 1024)
    files = {"file": ("big.png", big, "image/png")}
    resp = client.post("/v1/detect", files=files)
    assert resp.status_code == 413
