from __future__ import annotations

import os
import time
from typing import Any

import requests

from audit import log
from circuit import allow, fail, success

TIMEOUT = float(os.getenv("PAYMENT_TIMEOUT", "3"))
DEFAULT_HEADERS = {"Content-Type": "application/json"}



def send(endpoint: str, payload: dict[str, Any], retries: int = 3) -> dict[str, Any]:
    if not allow():
        log("payment_circuit_open", payload)
        return {"status": "circuit_open"}

    for attempt in range(retries):
        try:
            response = requests.post(endpoint, json=payload, headers=DEFAULT_HEADERS, timeout=TIMEOUT)
            if response.status_code == 200:
                success()
                log("payment_success", payload)
                return response.json()
        except requests.RequestException:
            pass

        fail()
        log("payment_fail", payload)
        time.sleep(2**attempt)

    return {"status": "failed"}
