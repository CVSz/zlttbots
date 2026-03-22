from __future__ import annotations

import time
from collections import defaultdict

from services.identity.did import verify

NONCES: set[str] = set()
RATE: dict[str, list[float]] = defaultdict(list)
REQUESTS_PER_SECOND = 10


def verify_signature(message_b64: str, signature_b64: str, public_key_b64: str) -> bool:
    import base64

    padding = "=" * (-len(public_key_b64) % 4)
    public_key = base64.urlsafe_b64decode(f"{public_key_b64}{padding}")
    return verify(public_key, message_b64, signature_b64)


def check_replay(nonce: str | None) -> bool:
    if not nonce or nonce in NONCES:
        return False
    NONCES.add(nonce)
    return True


def rate_limit(ip: str) -> bool:
    now = time.time()
    recent = [stamp for stamp in RATE[ip] if now - stamp < 1.0]
    RATE[ip] = recent
    if len(recent) >= REQUESTS_PER_SECOND:
        return False
    RATE[ip].append(now)
    return True
