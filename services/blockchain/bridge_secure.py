from __future__ import annotations

NONCES: dict[str, int] = {}


def verify_tx(chain: str, sender: str, nonce: int) -> bool:
    key = f"{chain}:{sender}"
    previous = NONCES.get(key)
    if previous is not None and nonce <= previous:
        return False
    NONCES[key] = nonce
    return True
