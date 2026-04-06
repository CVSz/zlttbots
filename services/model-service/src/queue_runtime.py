import json
import importlib.util
import logging
import os
from pathlib import Path
import threading
import time
from typing import Any, Callable

from confluent_kafka import Consumer, Producer

from result_store import result_store


def _load_local_metrics_module():
    module_path = Path(__file__).with_name("metrics.py")
    spec = importlib.util.spec_from_file_location("model_service_metrics", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load metrics module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_metrics = _load_local_metrics_module()
ASYNC_DLQ_TOTAL = _metrics.ASYNC_DLQ_TOTAL
ASYNC_RESULTS_TOTAL = _metrics.ASYNC_RESULTS_TOTAL

log = logging.getLogger("model-service.queue")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "redpanda:9092")
REQUEST_TOPIC = os.getenv("MODEL_REQUEST_TOPIC", "inference.request")
RESPONSE_TOPIC = os.getenv("MODEL_RESPONSE_TOPIC", "inference.response")
DLQ_TOPIC = os.getenv("MODEL_DLQ_TOPIC", "inference.dlq")
REQUEST_GROUP = os.getenv("MODEL_REQUEST_GROUP", "model-service-request-consumer")
RESPONSE_GROUP = os.getenv("MODEL_RESPONSE_GROUP", "model-service-response-consumer")
POLL_SECONDS = float(os.getenv("MODEL_CONSUMER_POLL_SECONDS", "0.2"))
_STARTED = False
_LOCK = threading.Lock()


def _consumer(group_id: str) -> Consumer:
    return Consumer(
        {
            "bootstrap.servers": KAFKA_BROKER,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
        }
    )


producer = Producer({"bootstrap.servers": KAFKA_BROKER})


def _decode_message(message: bytes) -> dict[str, Any]:
    payload = json.loads(message.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("message payload must be a JSON object")
    return payload


def _publish(topic: str, payload: dict[str, Any]) -> None:
    producer.produce(topic, json.dumps(payload).encode("utf-8"))
    producer.flush()


def _request_loop(predict_fn: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
    consumer = _consumer(REQUEST_GROUP)
    consumer.subscribe([REQUEST_TOPIC])
    log.info("Request consumer listening to %s via %s", REQUEST_TOPIC, KAFKA_BROKER)

    while True:
        msg = consumer.poll(POLL_SECONDS)
        if msg is None:
            continue
        if msg.error():
            log.warning("Kafka request consumer error: %s", msg.error())
            continue

        try:
            payload = _decode_message(msg.value())
            job_id = payload.get("job_id")
            features = payload.get("features")
            if not job_id or not isinstance(features, dict):
                raise ValueError("job_id and features object are required")

            result = predict_fn(features)
            response = {"job_id": job_id, "status": "done", **result}
            _publish(RESPONSE_TOPIC, response)
        except Exception as exc:  # pragma: no cover - thread failure path
            dlq_payload = {
                "job_id": payload.get("job_id") if 'payload' in locals() and isinstance(payload, dict) else None,
                "status": "failed",
                "error": str(exc),
                "failed_at": int(time.time()),
            }
            log.warning("Routing async job to DLQ: %s", dlq_payload)
            _publish(DLQ_TOPIC, dlq_payload)
            ASYNC_DLQ_TOTAL.inc()


def _response_loop() -> None:
    consumer = _consumer(RESPONSE_GROUP)
    consumer.subscribe([RESPONSE_TOPIC, DLQ_TOPIC])
    log.info("Response consumer listening to %s and %s", RESPONSE_TOPIC, DLQ_TOPIC)

    while True:
        msg = consumer.poll(POLL_SECONDS)
        if msg is None:
            continue
        if msg.error():
            log.warning("Kafka response consumer error: %s", msg.error())
            continue

        try:
            payload = _decode_message(msg.value())
            job_id = payload.get("job_id")
            if not job_id:
                raise ValueError("job_id is required")
            stored = result_store.set_result(job_id, payload)
            ASYNC_RESULTS_TOTAL.labels(stored.get("status", "unknown")).inc()
        except Exception:  # pragma: no cover - thread failure path
            log.warning("Failed to persist async result", exc_info=True)


def start_background_consumers(predict_fn: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
    global _STARTED
    with _LOCK:
        if _STARTED:
            return
        _STARTED = True

    for target in (_request_loop, _response_loop):
        kwargs = {"predict_fn": predict_fn} if target is _request_loop else {}
        thread = threading.Thread(target=target, kwargs=kwargs, daemon=True)
        thread.start()
