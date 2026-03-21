import json
import os
from typing import Any

from confluent_kafka import Producer

BROKER = os.getenv("KAFKA_BROKER", "redpanda:9092")
PRODUCER = Producer({"bootstrap.servers": BROKER})


def publish(topic: str, data: dict[str, Any]) -> None:
    if not topic:
        raise ValueError("topic is required")
    if not isinstance(data, dict):
        raise ValueError("data must be a dictionary")

    try:
        PRODUCER.produce(topic, json.dumps(data).encode("utf-8"))
        PRODUCER.flush(5)
    except Exception as exc:  # pragma: no cover - network dependent
        raise RuntimeError(f"Kafka publish failed: {exc}") from exc
