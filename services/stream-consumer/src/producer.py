import json
import os
from typing import Any

from confluent_kafka import Producer

producer = Producer({"bootstrap.servers": os.getenv("KAFKA_BROKER", "redpanda:9092")})


def emit_decision(data: dict[str, Any], topic: str = "decisions") -> None:
    producer.produce(topic, json.dumps(data).encode("utf-8"))
    producer.flush()
