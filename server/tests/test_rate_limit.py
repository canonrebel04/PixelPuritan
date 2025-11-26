import os
import time
from fastapi.testclient import TestClient
from server.main import app


def test_rate_limit_429(monkeypatch):
    # Tighten limits to force 429
    monkeypatch.setenv("PIXELPURITAN_RATE_LIMIT_RPS", "1")
    monkeypatch.setenv("PIXELPURITAN_RATE_LIMIT_BURST", "2")
    client = TestClient(app)

    files = {"file": ("x.png", b"123", "image/png")}
    # First two should pass, subsequent should hit 429
    r1 = client.post("/v1/detect", files=files)
    r2 = client.post("/v1/detect", files=files)
    r3 = client.post("/v1/detect", files=files)
    assert r1.status_code in (200, 413)  # may 413 due to small payload, but not 429
    assert r2.status_code in (200, 413)
    assert r3.status_code == 429
