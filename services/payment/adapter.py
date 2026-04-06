from __future__ import annotations

import os
import time
from typing import Any

import requests

from .audit import log
from .circuit import allow, fail, success

TIMEOUT = float(os.getenv("PAYMENT_TIMEOUT", "3"))
DEFAULT_HEADERS = {"Content-Type": "application/json"}



def send(endpoint: str, payload: dict[str, Any], retries: int = 3) -> dict[str, Any]:
    if retries < 1:
        raise ValueError("retries must be at least 1")

    if not allow():
        log("payment_circuit_open", payload)
        return {"status": "circuit_open"}

    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = requests.post(endpoint, json=payload, headers=DEFAULT_HEADERS, timeout=TIMEOUT)
            if response.status_code == 200:
                success()
                log("payment_success", payload)
                return response.json()
            fail()
            log("payment_fail", {**payload, "http_status": response.status_code})
        except requests.RequestException as exc:
            last_error = exc
            fail()
            log("payment_fail", {**payload, "error": str(exc)})
        time.sleep(2**attempt)

    if last_error is not None:
        log("payment_request_error", payload)
    return {"status": "failed"}
