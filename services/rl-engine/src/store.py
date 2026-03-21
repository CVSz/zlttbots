import json
import os
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg2
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://zttato:zttato@postgres:5432/zttato")
REDIS = redis.Redis.from_url(REDIS_URL, decode_responses=True)


@contextmanager
def db_connection() -> Iterator[Any]:
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def save_state(key: str, state: dict[str, Any]) -> None:
    REDIS.set(key, json.dumps(state))


def load_state(key: str) -> dict[str, Any] | None:
    raw = REDIS.get(key)
    return json.loads(raw) if raw else None


def log_decision(campaign_id: str, selected_campaign_id: str, score: float, features: dict[str, float]) -> None:
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO rl_decisions (campaign_id, selected_campaign_id, score, features)
                VALUES (%s, %s, %s, %s::jsonb)
                """,
                (campaign_id, selected_campaign_id, score, json.dumps(features)),
            )
