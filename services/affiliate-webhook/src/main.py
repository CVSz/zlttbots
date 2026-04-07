import hashlib
import hmac
import json
import os
from typing import Any

try:
    import psycopg2
except ModuleNotFoundError:  # pragma: no cover - dependency optional in unit tests
    psycopg2 = None
import requests
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

app = FastAPI(title="Affiliate Webhook (Verified)")

SECRET = os.getenv("AFFILIATE_WEBHOOK_SECRET", "")
DB_URL = os.getenv("DATABASE_URL", "postgresql://zlttbots:zlttbots@postgres:5432/zlttbots")
REWARD_COLLECTOR_URL = os.getenv("REWARD_COLLECTOR_URL", "http://reward-collector:8000/reward")
FEATURE_STORE_URL = os.getenv("FEATURE_STORE_URL", "http://feature-store:8000")
TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "10"))


class ConversionEvent(BaseModel):
    campaign_id: str = Field(min_length=1)
    revenue: float = Field(default=0.0, ge=0.0)
    clicks: int = Field(default=0, ge=0)
    views: int = Field(default=0, ge=0)
    conversions: int = Field(default=1, ge=1)
    source: str = Field(default="affiliate")
    affiliate_account_id: str | None = None
    order_id: str | None = None


def verify(signature: str, body: bytes) -> bool:
    mac = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, signature or "")


def db_connection():
    if psycopg2 is None:
        raise RuntimeError("psycopg2 is not installed")
    return psycopg2.connect(DB_URL)


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    db_ok = False
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("select 1")
                cur.fetchone()
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "service": "affiliate-webhook",
        "checks": {"db": db_ok},
    }


@app.post("/conversion")
async def conversion(req: Request) -> dict[str, bool]:
    body = await req.body()
    signature = req.headers.get("X-Signature", "")
    if not verify(signature, body):
        raise HTTPException(status_code=401, detail="invalid signature")

    event = ConversionEvent.model_validate(json.loads(body.decode()))

    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO campaign_metrics (campaign_id, views, clicks, conversions, revenue)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (event.campaign_id, event.views, event.clicks, event.conversions, event.revenue),
            )

    try:
        feature_response = requests.post(
            f"{FEATURE_STORE_URL}/features/{event.campaign_id}",
            json={
                "views": event.views,
                "clicks": event.clicks,
                "conversions": event.conversions,
                "revenue": event.revenue,
                "mode": "increment",
            },
            timeout=TIMEOUT,
        )
        feature_response.raise_for_status()

        response = requests.post(
            REWARD_COLLECTOR_URL,
            json={
                "campaign_id": event.campaign_id,
                "revenue": event.revenue,
                "conversions": event.conversions,
                "clicks": event.clicks,
                "views": event.views,
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"downstream service unavailable: {exc}") from exc

    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9700)
