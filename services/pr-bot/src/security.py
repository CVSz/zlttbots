from __future__ import annotations

import hashlib
import hmac


def verify_webhook_signature(secret: str, payload: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    expected = f"sha256={digest}"
    return hmac.compare_digest(expected, signature)
