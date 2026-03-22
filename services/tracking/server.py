from __future__ import annotations

import json
import logging
import os
import time
import uuid
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse

logger = logging.getLogger("tracking.server")

AFFILIATE_BASE_URL = os.getenv("AFFILIATE_BASE_URL", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
app = FastAPI(title="Tracking Service")


def _connect():
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="database url not configured")
    try:
        import psycopg2  # type: ignore

        return psycopg2.connect(DATABASE_URL)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="database driver unavailable") from exc


def _assert_campaign_id(campaign_id: str) -> str:
    cid = campaign_id.strip()
    if not cid:
        raise HTTPException(status_code=422, detail="campaign_id is required")
    if len(cid) > 64 or not cid.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(status_code=422, detail="campaign_id format is invalid")
    return cid


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "tracking"}


@app.get("/t/{campaign_id}")
async def track(campaign_id: str, request: Request) -> RedirectResponse:
    if not AFFILIATE_BASE_URL:
        raise HTTPException(status_code=500, detail="affiliate base url not configured")

    cid = _assert_campaign_id(campaign_id)
    click_id = str(uuid.uuid4())
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO clicks(id, campaign_id, ip, ua, ts)
                VALUES(%s, %s, %s, %s, %s)
                """,
                (click_id, cid, ip, ua, int(time.time())),
            )
        conn.commit()

    query = urlencode({"cid": cid, "click_id": click_id})
    target = f"{AFFILIATE_BASE_URL}?{query}"
    logger.info(json.dumps({"event": "click_tracked", "campaign_id": cid, "click_id": click_id}))
    return RedirectResponse(target, status_code=307)
