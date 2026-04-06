from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any

import psycopg2


@dataclass(frozen=True)
class ProductPayoutRecord:
    network: str
    product_id: str
    payout_rate: float
    currency: str
    freshness_ts: datetime


@dataclass(frozen=True)
class PublishingJob:
    tenant_id: str
    product_id: str
    video_id: str
    destination_url: str
    retry_count: int = 0


class InMemoryStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self.products: list[dict[str, Any]] = []
        self.arbitrage_events: list[dict[str, Any]] = []
        self.product_payouts: dict[tuple[str, str], ProductPayoutRecord] = {}
        self.publish_jobs: dict[str, list[PublishingJob]] = defaultdict(list)
        self.publish_counters: dict[tuple[str, str], int] = defaultdict(int)
        self.dead_letters: list[dict[str, Any]] = []
        self.videos: dict[str, dict[str, Any]] = {}
        self.publish_results: list[dict[str, Any]] = []
        self.performance: dict[tuple[str, str], dict[str, float]] = {}

    def seed_products(self, products: list[dict[str, Any]]) -> None:
        with self._lock:
            self.products = list(products)


MEMORY_STORE = InMemoryStore()
USE_INMEMORY_DB = os.getenv("USE_INMEMORY_DB", "0") == "1"


def get_db():
    return psycopg2.connect(os.environ["DB_URL"])


def fetch_products() -> list[dict[str, Any]]:
    if USE_INMEMORY_DB:
        return list(MEMORY_STORE.products)

    with get_db() as db:
        with db.cursor() as cur:
            cur.execute(
                """
                select id,name,price,source
                from products
                """
            )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "name": row[1],
            "price": float(row[2]),
            "source": row[3],
        }
        for row in rows
    ]


def insert_event(event: dict[str, Any]) -> None:
    if USE_INMEMORY_DB:
        MEMORY_STORE.arbitrage_events.append(dict(event))
        return

    with get_db() as db:
        with db.cursor() as cur:
            cur.execute(
                """
                insert into arbitrage_events
                (product_name,buy_source,sell_source,buy_price,sell_price,profit)
                values(%s,%s,%s,%s,%s,%s)
                """,
                (
                    event["product"],
                    event["buy"],
                    event["sell"],
                    event["buy_price"],
                    event["sell_price"],
                    event["profit"],
                ),
            )


def list_events(limit: int = 50) -> list[dict[str, Any]]:
    if USE_INMEMORY_DB:
        sorted_events = sorted(MEMORY_STORE.arbitrage_events, key=lambda event: float(event.get("profit", 0)), reverse=True)
        return [dict(event) for event in sorted_events[:limit]]

    with get_db() as db:
        with db.cursor() as cur:
            cur.execute(
                """
                select product_name,buy_source,sell_source,buy_price,sell_price,profit
                from arbitrage_events
                order by profit desc
                limit %s
                """,
                (limit,),
            )
            rows = cur.fetchall()

    return [
        {
            "product": row[0],
            "buy": row[1],
            "sell": row[2],
            "buy_price": float(row[3]),
            "sell_price": float(row[4]),
            "profit": float(row[5]),
        }
        for row in rows
    ]


def upsert_product_payout(record: ProductPayoutRecord) -> None:
    if USE_INMEMORY_DB:
        MEMORY_STORE.product_payouts[(record.network, record.product_id)] = record
        return
    with get_db() as db:
        with db.cursor() as cur:
            cur.execute(
                """
                insert into affiliate_product_payouts
                    (network, product_id, payout_rate, currency, freshness_ts)
                values (%s, %s, %s, %s, %s)
                on conflict (network, product_id)
                do update set payout_rate = excluded.payout_rate,
                              currency = excluded.currency,
                              freshness_ts = excluded.freshness_ts
                """,
                (record.network, record.product_id, record.payout_rate, record.currency, record.freshness_ts),
            )


def get_product_payout(network: str, product_id: str) -> float | None:
    if USE_INMEMORY_DB:
        record = MEMORY_STORE.product_payouts.get((network, product_id))
        return None if record is None else record.payout_rate

    with get_db() as db:
        with db.cursor() as cur:
            cur.execute(
                """
                select payout_rate
                from affiliate_product_payouts
                where network = %s and product_id = %s
                """,
                (network, product_id),
            )
            row = cur.fetchone()
    return None if row is None else float(row[0])


def enqueue_publish_job(job: PublishingJob) -> None:
    MEMORY_STORE.publish_jobs[job.tenant_id].append(job)


def dequeue_publish_jobs(tenant_id: str, max_items: int) -> list[PublishingJob]:
    queue = MEMORY_STORE.publish_jobs[tenant_id]
    drained = queue[:max_items]
    del queue[:max_items]
    return drained


def increase_daily_counter(tenant_id: str, day_key: str) -> int:
    counter_key = (tenant_id, day_key)
    MEMORY_STORE.publish_counters[counter_key] += 1
    return MEMORY_STORE.publish_counters[counter_key]


def get_daily_counter(tenant_id: str, day_key: str) -> int:
    return MEMORY_STORE.publish_counters[(tenant_id, day_key)]


def put_dead_letter(entry: dict[str, Any]) -> None:
    MEMORY_STORE.dead_letters.append(entry)


def record_publish_result(result: dict[str, Any]) -> None:
    MEMORY_STORE.publish_results.append(result)


def record_video(video_id: str, payload: dict[str, Any]) -> None:
    MEMORY_STORE.videos[video_id] = payload


def record_performance(tenant_id: str, product_id: str, payload: dict[str, float]) -> None:
    MEMORY_STORE.performance[(tenant_id, product_id)] = payload


def get_posted_product_reporting(tenant_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for publish_result in MEMORY_STORE.publish_results:
        if publish_result["tenant_id"] != tenant_id:
            continue
        product_id = publish_result["product_id"]
        video_id = publish_result["video_id"]
        payout = MEMORY_STORE.product_payouts.get((publish_result["network"], product_id))
        performance = MEMORY_STORE.performance.get((tenant_id, product_id), {})
        rows.append(
            {
                "tenant_id": tenant_id,
                "product_id": product_id,
                "video_id": video_id,
                "publish_status": publish_result["status"],
                "publish_external_id": publish_result.get("external_id"),
                "clicks": int(performance.get("clicks", 0)),
                "conversions": int(performance.get("conversions", 0)),
                "revenue": float(performance.get("revenue", 0.0)),
                "commission_rate": 0.0 if payout is None else payout.payout_rate,
                "commission_freshness_ts": None if payout is None else payout.freshness_ts.isoformat(),
            }
        )

    rows.sort(key=lambda row: (row["product_id"], row["video_id"]))
    return rows


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
