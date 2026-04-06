from __future__ import annotations

import importlib

import pytest

from services.payment import adapter, circuit


def test_payment_modules_importable() -> None:
    importlib.import_module("services.payment.adapter")
    importlib.import_module("services.payment.main")


def test_circuit_opens_at_failure_threshold() -> None:
    circuit.FAILS = 0
    circuit.OPEN = False
    circuit.LAST_FAIL = 0.0

    for _ in range(circuit.MAX_FAILURES):
        circuit.fail(now=100.0)

    assert circuit.OPEN is True
    assert circuit.allow(now=100.0 + circuit.RESET_AFTER_SECONDS - 1) is False


def test_send_rejects_invalid_retry_count() -> None:
    with pytest.raises(ValueError, match="retries must be at least 1"):
        adapter.send("https://payments.example/stripe", {"campaign_id": "cmp-1"}, retries=0)


def test_send_returns_failed_after_http_5xx(monkeypatch: pytest.MonkeyPatch) -> None:
    class StubResponse:
        status_code = 503

    monkeypatch.setattr(adapter, "allow", lambda: True)
    monkeypatch.setattr(adapter, "fail", lambda: None)
    monkeypatch.setattr(adapter, "success", lambda: None)
    monkeypatch.setattr(adapter, "log", lambda *args, **kwargs: None)
    monkeypatch.setattr(adapter.time, "sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(adapter.requests, "post", lambda *args, **kwargs: StubResponse())

    response = adapter.send("https://payments.example/stripe", {"campaign_id": "cmp-1"}, retries=1)

    assert response == {"status": "failed"}
