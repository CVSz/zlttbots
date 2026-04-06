import importlib.util
from pathlib import Path

import pytest
import requests

MODULE_PATH = Path("services/network-egress/src/client.py")
SPEC = importlib.util.spec_from_file_location("network_egress_client", MODULE_PATH)
client_module = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(client_module)

SafeHttpClient = client_module.SafeHttpClient


class _Response:
    def __init__(self, status_code: int):
        self.status_code = status_code


def test_retries_on_server_error_and_succeeds(monkeypatch):
    calls = {"count": 0}

    def fake_post(url, json=None, headers=None, timeout=0):
        calls["count"] += 1
        if calls["count"] < 3:
            return _Response(503)
        return _Response(200)

    monkeypatch.setattr(client_module.requests, "post", fake_post)
    monkeypatch.setattr(client_module.time, "sleep", lambda _: None)

    client = SafeHttpClient(retries=3, backoff=0, allowed_hosts={"api.example.com"})
    response = client.post("https://api.example.com/webhook", json={"ok": True})
    assert response.status_code == 200
    assert calls["count"] == 3


def test_raises_after_retry_exhaustion(monkeypatch):
    def failing_post(url, json=None, headers=None, timeout=0):
        raise requests.RequestException("network down")

    monkeypatch.setattr(client_module.requests, "post", failing_post)
    monkeypatch.setattr(client_module.time, "sleep", lambda _: None)

    client = SafeHttpClient(retries=2, backoff=0)
    with pytest.raises(RuntimeError, match="request failed after retries"):
        client.post("https://api.partner.example/publish")


def test_blocks_disallowed_host():
    client = SafeHttpClient(allowed_hosts={"api.example.com"})
    with pytest.raises(ValueError, match="not allowed"):
        client.post("https://evil.example.net/collect")


def test_blocks_private_address():
    client = SafeHttpClient()
    with pytest.raises(ValueError, match="private or loopback"):
        client.post("http://127.0.0.1:8080/admin")
