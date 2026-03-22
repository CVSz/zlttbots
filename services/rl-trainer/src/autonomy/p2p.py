from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GossipEnvelope:
    topic: str
    max_hops: int
    signed: bool


def default_envelope(topic: str) -> GossipEnvelope:
    return GossipEnvelope(topic=topic, max_hops=3, signed=True)
