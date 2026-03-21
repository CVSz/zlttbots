import json
import logging
import os
from typing import Any

from confluent_kafka import Producer

log = logging.getLogger("reward-collector.kafka")
BROKER = os.getenv("KAFKA_BROKER", "redpanda:9092")
FEEDBACK_TOPIC = os.getenv("KAFKA_FEEDBACK_TOPIC", "feedback")
producer = Producer({"bootstrap.servers": BROKER})


def emit_feedback(data: dict[str, Any]) -> None:
    try:
        producer.produce(FEEDBACK_TOPIC, json.dumps(data).encode("utf-8"))
        producer.flush()
    except Exception as exc:  # pragma: no cover - defensive logging
        log.warning("Failed to emit feedback event: %s", exc)
