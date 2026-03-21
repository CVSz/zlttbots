import hashlib
import hmac
import json
import os
from typing import Any

import psycopg2
import uvicorn
from fastapi import FastAPI, HTTPException, Request

app = FastAPI(title="Affiliate Webhook (Verified)")

SECRET = os.getenv("AFFILIATE_WEBHOOK_SECRET", "")
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://zttato:zttato@postgres:5432/zttato",
)


def verify(signature: str, body: bytes) -> bool:
    mac = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, signature or "")


def db_connection():
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

    data = json.loads(body.decode())
    campaign_id = data["campaign_id"]
    revenue = float(data.get("revenue", 0))

    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO campaign_metrics (campaign_id, views, clicks, conversions, revenue)
                VALUES (%s, 0, 0, 1, %s)
                """,
                (campaign_id, revenue),
            )

    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9700)
