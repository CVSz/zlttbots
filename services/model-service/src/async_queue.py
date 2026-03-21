import json
import os
import uuid
from dataclasses import dataclass

from confluent_kafka import Producer

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "redpanda:9092")
REQUEST_TOPIC = os.getenv("ASYNC_INFERENCE_REQUEST_TOPIC", "inference.request")


class AsyncInferenceUnavailable(RuntimeError):
    pass


@dataclass
class AsyncInferenceProducer:
    enabled: bool
    producer: Producer | None = None
    request_topic: str = REQUEST_TOPIC

    @classmethod
    def from_env(cls, enabled: bool) -> "AsyncInferenceProducer":
        if not enabled:
            return cls(enabled=False)
        return cls(
            enabled=True,
            producer=Producer({"bootstrap.servers": KAFKA_BROKER}),
            request_topic=REQUEST_TOPIC,
        )

    def enqueue(self, features: list[float]) -> str:
        if not self.enabled or self.producer is None:
            raise AsyncInferenceUnavailable(
                "Async inference is disabled. Set ASYNC_INFERENCE_ENABLED=true and configure Kafka first."
            )
        job_id = str(uuid.uuid4())
        payload = {"job_id": job_id, "features": features}
        self.producer.produce(self.request_topic, json.dumps(payload).encode("utf-8"))
        self.producer.flush()
        return job_id
