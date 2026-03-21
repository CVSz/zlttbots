import json
import logging
import os
from typing import Any

from confluent_kafka import Producer

log = logging.getLogger("master-orchestrator.kafka")
BROKER = os.getenv("KAFKA_BROKER", "redpanda:9092")
DECISIONS_TOPIC = os.getenv("KAFKA_DECISIONS_TOPIC", "decisions")
producer = Producer({"bootstrap.servers": BROKER})


def emit_decision(data: dict[str, Any]) -> None:
    try:
        producer.produce(DECISIONS_TOPIC, json.dumps(data).encode("utf-8"))
        producer.flush()
    except Exception as exc:  # pragma: no cover - defensive logging
        log.warning("Failed to emit decision event: %s", exc)
