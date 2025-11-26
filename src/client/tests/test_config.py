import os
from importlib import reload
import src.client.nsfw_tool as nsfw_tool


def test_env_config_overrides(monkeypatch):
    monkeypatch.setenv("PIXELPURITAN_API_URL", "http://example:1234/v1/detect")
    monkeypatch.setenv("PIXELPURITAN_CONCURRENCY", "7")
    reload(nsfw_tool)
    assert nsfw_tool.API_URL == "http://example:1234/v1/detect"
    assert nsfw_tool.CONCURRENT_REQUESTS == 7
