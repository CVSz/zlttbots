from __future__ import annotations

import json
import os

from confluent_kafka import Consumer, Producer

BOOT = os.getenv("KAFKA_BOOT", "redpanda:9092")

producer = Producer({"bootstrap.servers": BOOT, "enable.idempotence": True})
consumer = Consumer(
    {
        "bootstrap.servers": BOOT,
        "group.id": "pipeline",
        "auto.offset.reset": "earliest",
    }
)

SCHEMA = {"title": str, "media_url": str}



def validate(item: dict) -> bool:
    return all(key in item for key in SCHEMA)



def label(item: dict) -> dict:
    item["label"] = 1 if item.get("engagement", 0) > 0.3 else 0
    return item



def run() -> None:
    consumer.subscribe(["raw"])
    while True:
        message = consumer.poll(1.0)
        if not message:
            continue
        data = json.loads(message.value())
        if validate(data):
            producer.produce("clean", json.dumps(label(data)).encode())
