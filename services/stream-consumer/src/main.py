import json
import logging
import os
import signal
import sys
from contextlib import contextmanager
from typing import Any, Iterator, Literal

import psycopg2
import redis
from confluent_kafka import Consumer, KafkaException
from pydantic import BaseModel, ConfigDict, ValidationError

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger("stream-consumer")

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "redpanda:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "events")
KAFKA_GROUP = os.getenv("KAFKA_GROUP", "zttato-consumer")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://zttato:zttato@postgres:5432/zttato")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
REDIS = redis.Redis.from_url(REDIS_URL, decode_responses=True)
RUNNING = True


class CampaignEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    campaign_id: str
    type: Literal["view", "click", "conversion"]


@contextmanager
def db_connection() -> Iterator[Any]:
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def shutdown(*_: Any) -> None:
    global RUNNING
    RUNNING = False
    log.info("Shutdown signal received")


def update_online_features(campaign_id: str, event_type: str) -> dict[str, int]:
    key = f"campaign:{campaign_id}:features"
    try:
        with REDIS.pipeline() as pipe:
            while True:
                try:
                    pipe.watch(key)
                    current = pipe.hgetall(key)
                    views = int(current.get("views", 0))
                    clicks = int(current.get("clicks", 0))
                    conversions = int(current.get("conv", 0))

                    if event_type == "view":
                        views += 1
                    elif event_type == "click":
                        clicks += 1
                    elif event_type == "conversion":
                        conversions += 1

                    pipe.multi()
                    pipe.hset(
                        key,
                        mapping={"views": views, "clicks": clicks, "conv": conversions},
                    )
                    pipe.execute()
                    return {"views": views, "clicks": clicks, "conversions": conversions}
                except redis.WatchError:
                    log.warning("Redis conflict on %s, retrying", key)
                    continue
                finally:
                    pipe.reset()
    except redis.RedisError as exc:
        raise RuntimeError(f"Failed to update Redis features: {exc}") from exc


def persist_offline_metrics(campaign_id: str, metrics: dict[str, int]) -> None:
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO campaign_metrics (campaign_id, views, clicks, conversions)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    campaign_id,
                    metrics["views"],
                    metrics["clicks"],
                    metrics["conversions"],
                ),
            )


def process(raw_event: dict[str, Any]) -> None:
    event = CampaignEvent.model_validate(raw_event)
    metrics = update_online_features(event.campaign_id, event.type)
    persist_offline_metrics(event.campaign_id, metrics)
    log.info("Processed event campaign_id=%s type=%s metrics=%s", event.campaign_id, event.type, metrics)


def create_consumer() -> Consumer:
    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_BROKER,
            "group.id": KAFKA_GROUP,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([KAFKA_TOPIC])
    return consumer


def main() -> int:
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    consumer = create_consumer()
    log.info("Stream consumer listening topic=%s broker=%s", KAFKA_TOPIC, KAFKA_BROKER)

    try:
        while RUNNING:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())

            try:
                payload = json.loads(msg.value().decode("utf-8"))
                process(payload)
                consumer.commit(message=msg)
            except (json.JSONDecodeError, ValidationError, RuntimeError, psycopg2.Error) as exc:
                log.exception("Failed to process message at offset=%s: %s", msg.offset(), exc)
    finally:
        consumer.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
