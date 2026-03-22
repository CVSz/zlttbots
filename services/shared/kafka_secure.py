from __future__ import annotations

import json
from typing import Any

from confluent_kafka import Producer

producer = Producer(
    {
        "bootstrap.servers": "redpanda:9092",
        "enable.idempotence": True,
    }
)
DLQ = "dead_letter"


def safe_produce(topic: str, data: dict[str, Any]) -> None:
    payload = json.dumps(data).encode()
    try:
        producer.produce(topic, payload)
    except Exception:
        producer.produce(DLQ, payload)
