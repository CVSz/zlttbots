import logging
import os
import time
from threading import Lock
from typing import Any
from typing import Optional

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Execution Engine (Compliant)")
log = logging.getLogger("execution-engine")
logging.basicConfig(level=logging.INFO)

API_BASE = os.getenv("PLATFORM_API_BASE", "https://api.partner.example")
API_KEY = os.getenv("PLATFORM_API_KEY", "")
TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "10"))
MAX_TOKENS = int(os.getenv("RATE_MAX_TOKENS", "120"))
TOKENS = int(os.getenv("RATE_TOKENS", str(min(60, MAX_TOKENS))))
LAST_REFILL = time.time()
REFILL_RATE = float(os.getenv("RATE_REFILL_PER_SEC", "1"))
TOKEN_LOCK = Lock()


class PublishRequest(BaseModel):
    campaign_id: str = Field(min_length=1)
    video_url: str = Field(min_length=1)
    caption: str = Field(min_length=1, max_length=2200)
    destination_url: str = Field(min_length=1)


class PublishResponse(BaseModel):
    ok: bool
    external_id: Optional[str] = None
    status: str


def http_post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Upstream error: {response.text}")

    return response.json()


def acquire_token() -> None:
    global TOKENS, LAST_REFILL

    with TOKEN_LOCK:
        now = time.time()
        delta = now - LAST_REFILL
        refill = int(delta * REFILL_RATE)
        if refill > 0:
            TOKENS = min(MAX_TOKENS, TOKENS + refill)
            LAST_REFILL = now

        if TOKENS <= 0:
            raise HTTPException(status_code=429, detail="Rate limited")

        TOKENS -= 1


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "execution-engine",
        "config": {
            "api_base": API_BASE,
            "timeout": TIMEOUT,
            "max_tokens": MAX_TOKENS,
            "refill_rate": REFILL_RATE,
        },
    }


@app.post("/publish", response_model=PublishResponse)
def publish(req: PublishRequest) -> PublishResponse:
    acquire_token()

    payload = {
        "video_url": req.video_url,
        "caption": req.caption,
        "destination_url": req.destination_url,
        "metadata": {"campaign_id": req.campaign_id},
    }

    log.info("Publishing campaign=%s", req.campaign_id)
    data = http_post(f"{API_BASE}/content/publish", payload)

    return PublishResponse(
        ok=True,
        external_id=data.get("id"),
        status=data.get("status", "submitted"),
    )


@app.get("/status/{external_id}")
def status(external_id: str) -> dict[str, Any]:
    acquire_token()
    return http_post(f"{API_BASE}/content/status", {"id": external_id})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9600)
