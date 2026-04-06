from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class Target:
    name: str
    url: str


ALLOWED_ENVIRONMENTS = {"staging", "sandbox"}
TARGETS = (
    Target("model-service", "http://model-service:8000/predict"),
    Target("exchange", "http://exchange:8000/order"),
)


def allow(environment: str) -> bool:
    return environment in ALLOWED_ENVIRONMENTS


def sample_payload(seed: str) -> dict[str, int]:
    if not seed:
        raise ValueError("seed must be a non-empty string")
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    views = int.from_bytes(digest[0:4], "big") % 1_000_001
    clicks = int.from_bytes(digest[4:8], "big") % 1_001
    conversions = int.from_bytes(digest[8:12], "big") % 101
    return {
        "views": views,
        "clicks": clicks,
        "conversions": conversions,
    }


def plan(environment: str) -> list[dict[str, object]]:
    if not allow(environment):
        return []
    return [
        {
            "target": target.name,
            "url": target.url,
            "payload": sample_payload(f"{environment}:{target.name}:{target.url}"),
        }
        for target in TARGETS
    ]
