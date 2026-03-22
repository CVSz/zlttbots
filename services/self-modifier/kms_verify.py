from __future__ import annotations

import os

import requests

KMS_ENDPOINT = os.getenv("KMS_ENDPOINT", "")
REQUEST_TIMEOUT = float(os.getenv("KMS_TIMEOUT", "5"))



def verify(patch: str, signature: str) -> bool:
    if not KMS_ENDPOINT:
        return False

    response = requests.post(
        f"{KMS_ENDPOINT.rstrip('/')}/verify",
        json={"data": patch, "signature": signature},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return bool(response.json().get("valid", False))
