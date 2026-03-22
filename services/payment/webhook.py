from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Request

logger = logging.getLogger("payment.webhook")

app = FastAPI(title="Payment Webhook")


class DBExecutor:
    def execute(self, query: str, params: tuple[Any, ...]) -> None:  # pragma: no cover - protocol-like helper
        raise NotImplementedError


def _verify_event(payload: bytes, signature: str | None) -> dict[str, Any]:
    if not signature:
        raise HTTPException(status_code=400, detail="missing stripe-signature")

    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(status_code=500, detail="stripe webhook secret not configured")

    try:
        import stripe  # type: ignore

        event = stripe.Webhook.construct_event(payload, signature, secret)
        return dict(event)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("stripe webhook signature verification failed")
        raise HTTPException(status_code=400, detail="invalid webhook signature") from exc


def _persist_order(db: DBExecutor, campaign_id: str, click_id: str, amount: float, event_id: str) -> None:
    db.execute(
        """
        INSERT INTO payment_events(event_id, processed_at)
        VALUES(%s, %s)
        ON CONFLICT (event_id) DO NOTHING
        """,
        (event_id, int(time.time())),
    )
    db.execute(
        """
        INSERT INTO orders(campaign_id, click_id, amount, ts)
        VALUES(%s, %s, %s, %s)
        """,
        (campaign_id, click_id, amount, int(time.time())),
    )


def _default_db() -> DBExecutor:
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        raise HTTPException(status_code=500, detail="database url not configured")

    try:
        import psycopg2  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="psycopg2 is required") from exc

    class _ConnExecutor(DBExecutor):
        def execute(self, query: str, params: tuple[Any, ...]) -> None:
            with psycopg2.connect(database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                conn.commit()

    return _ConnExecutor()


@app.post("/webhook")
async def stripe_webhook(request: Request) -> dict[str, bool]:
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    event = _verify_event(payload, signature)

    if event.get("type") != "payment_intent.succeeded":
        return {"ok": True}

    data_object = event.get("data", {}).get("object", {})
    metadata = data_object.get("metadata", {})
    campaign_id = str(metadata.get("campaign_id", "")).strip()
    click_id = str(metadata.get("click_id", "")).strip()
    amount = float(data_object.get("amount", 0)) / 100.0
    event_id = str(event.get("id", "")).strip()

    if not campaign_id or not click_id or not event_id:
        logger.error(
            "payment webhook missing required metadata",
            extra={"campaign_id": campaign_id, "click_id": click_id, "event_id": event_id},
        )
        raise HTTPException(status_code=422, detail="campaign_id, click_id, and event_id are required")

    db = _default_db()
    _persist_order(db, campaign_id=campaign_id, click_id=click_id, amount=amount, event_id=event_id)
    logger.info(json.dumps({"event": "payment_recorded", "campaign_id": campaign_id, "click_id": click_id, "amount": amount}))
    return {"ok": True}
