from __future__ import annotations

import random
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


def sample_payload() -> dict[str, int]:
    return {
        "views": random.randint(0, 1_000_000),
        "clicks": random.randint(0, 1_000),
        "conversions": random.randint(0, 100),
    }


def plan(environment: str) -> list[dict[str, object]]:
    if not allow(environment):
        return []
    return [{"target": target.name, "url": target.url, "payload": sample_payload()} for target in TARGETS]
