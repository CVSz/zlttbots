from __future__ import annotations

import os
import time
from datetime import date
from threading import Lock

import psycopg2
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from connectors.client import UnifiedAffiliateClient
from connectors.contracts import AffiliateNetwork, ProductCommission
from core.database import (
    MEMORY_STORE,
    ProductPayoutRecord,
    PublishingJob,
    fetch_products,
    get_daily_counter,
    get_product_payout,
    get_posted_product_reporting,
    insert_event,
    list_events,
    record_performance,
    record_video,
    upsert_product_payout,
)
from engine.arbitrage import detect
from metrics import request_counter, request_latency
from publishing.controller import DailyPublishingController

app = FastAPI()
client = UnifiedAffiliateClient()
controller = DailyPublishingController()
_readiness_lock = Lock()
_is_ready = False


class PayoutIngestRequest(BaseModel):
    network: AffiliateNetwork
    product_id: str = Field(min_length=1, max_length=128)
    payout_rate: float = Field(ge=0, le=1)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class AffiliateSyncRequest(BaseModel):
    network: AffiliateNetwork
    auth_token: str = Field(min_length=16)


class PublishJobRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    video_id: str = Field(min_length=1)
    destination_url: str = Field(min_length=1)


class DailyRunRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    simulation: "PublishSimulationResult"


class PerformanceIngestRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    clicks: int = Field(ge=0)
    conversions: int = Field(ge=0)
    revenue: float = Field(ge=0)


class VideoIngestRequest(BaseModel):
    video_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=256)


class PublishSimulationResult(BaseModel):
    status: str = Field(default="submitted")
    external_id: str | None = None
    network: AffiliateNetwork = AffiliateNetwork.TIKTOK


class ArbitrageScanRequest(BaseModel):
    persist: bool = True
    min_profit: float = Field(default=1.0, ge=0)
    max_results: int = Field(default=100, ge=1, le=2000)


def get_db():
    return psycopg2.connect(os.environ["DB_URL"])


def _probe_database() -> bool:
    try:
        with get_db() as db:
            with db.cursor() as cur:
                cur.execute('select 1')
                cur.fetchone()
        return True
    except Exception:
        return False


@app.on_event("startup")
def startup_probe() -> None:
    global _is_ready
    # Retry dependency checks to avoid failing health checks during cold start.
    for _ in range(30):
        if _probe_database():
            with _readiness_lock:
                _is_ready = True
            return
        time.sleep(2)


@app.get('/health/live')
def health_live():
    return {"status": "alive", "service": "arbitrage-engine"}


@app.get('/health/ready')
def health_ready():
    with _readiness_lock:
        ready = _is_ready
    if not ready:
        raise HTTPException(status_code=503, detail="service is starting")
    return {"status": "ready", "service": "arbitrage-engine"}


@app.get('/healthz')
def healthz():
    db_ok = False

    db_ok = _probe_database()

    return {
        'status': 'ok' if db_ok else 'degraded',
        'service': 'arbitrage-engine',
        'checks': {
            'db': db_ok,
        },
    }


@app.get('/metrics')
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get('/arbitrage')
def list_arbitrage_events():
    start = time.perf_counter()
    result = list_events(limit=50)
    request_counter.inc()
    request_latency.observe(time.perf_counter() - start)
    return result


@app.post('/arbitrage/scan')
def scan_arbitrage(payload: ArbitrageScanRequest):
    start = time.perf_counter()
    products = fetch_products()
    opportunities = detect(products, get_product_payout, min_profit=payload.min_profit)
    opportunities.sort(key=lambda item: float(item["profit"]), reverse=True)
    selected = opportunities[: payload.max_results]
    inserted = 0

    if payload.persist:
        for event in selected:
            insert_event(event)
            inserted += 1

    request_counter.inc()
    request_latency.observe(time.perf_counter() - start)
    return {
        "ok": True,
        "products_scanned": len(products),
        "opportunities_found": len(opportunities),
        "returned": len(selected),
        "persisted": inserted,
        "results": selected,
    }


@app.post('/affiliate/payouts/ingest')
def ingest_payout(payload: PayoutIngestRequest):
    record = ProductCommission(
        network=payload.network,
        product_id=payload.product_id,
        payout_rate=payload.payout_rate,
        currency=payload.currency,
    )
    upsert_product_payout(
        ProductPayoutRecord(
            network=record.network.value,
            product_id=record.product_id,
            payout_rate=record.payout_rate,
            currency=record.currency,
            freshness_ts=record.fetched_at,
        )
    )
    return {"ok": True, "freshness_ts": record.fetched_at.isoformat()}


@app.post('/affiliate/sync')
def sync_affiliate(payload: AffiliateSyncRequest):
    snapshot = client.fetch_network_snapshot(payload.network, payload.auth_token)
    for commission in snapshot.commissions:
        upsert_product_payout(
            ProductPayoutRecord(
                network=commission.network.value,
                product_id=commission.product_id,
                payout_rate=commission.payout_rate,
                currency=commission.currency,
                freshness_ts=commission.fetched_at,
            )
        )
    return {
        "ok": True,
        "network": payload.network,
        "commissions": len(snapshot.commissions),
        "orders": len(snapshot.orders),
        "fetched_at": snapshot.fetched_at.isoformat(),
    }


@app.post('/publishing/jobs')
def enqueue_publish_job(payload: PublishJobRequest):
    from core.database import enqueue_publish_job as queue_push

    queue_push(PublishingJob(**payload.model_dump()))
    return {"ok": True}


@app.post('/publishing/run-daily')
def run_daily(payload: DailyRunRequest):
    def publish_fn(job: PublishingJob) -> dict:
        return payload.simulation.model_dump()

    result = controller.run_for_tenant(payload.tenant_id, publish_fn)
    return result


@app.get('/publishing/counters/{tenant_id}')
def get_counter(tenant_id: str):
    day_key = date.today().isoformat()
    return {"tenant_id": tenant_id, "day": day_key, "published": get_daily_counter(tenant_id, day_key)}


@app.post('/videos')
def ingest_video(payload: VideoIngestRequest):
    record_video(payload.video_id, payload.model_dump())
    return {"ok": True}


@app.post('/performance')
def ingest_performance(payload: PerformanceIngestRequest):
    record_performance(
        tenant_id=payload.tenant_id,
        product_id=payload.product_id,
        payload={"clicks": payload.clicks, "conversions": payload.conversions, "revenue": payload.revenue},
    )
    return {"ok": True}


@app.get('/reporting/posted-products/{tenant_id}')
def posted_product_reporting(tenant_id: str):
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id required")
    return {
        "tenant_id": tenant_id,
        "rows": get_posted_product_reporting(tenant_id),
        "dead_letters": [entry for entry in MEMORY_STORE.dead_letters if entry["tenant_id"] == tenant_id],
    }
