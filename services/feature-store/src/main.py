import os
from typing import Any

import redis
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Feature Store")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
REDIS = redis.Redis.from_url(REDIS_URL, decode_responses=True)


class CampaignFeatures(BaseModel):
    views: int = 0
    clicks: int = 0
    conversions: int = 0


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    try:
        redis_ok = bool(REDIS.ping())
    except redis.RedisError:
        redis_ok = False

    return {"status": "ok" if redis_ok else "degraded", "service": "feature-store", "checks": {"redis": redis_ok}}


@app.get("/features/{campaign_id}", response_model=CampaignFeatures)
def get_features(campaign_id: str) -> CampaignFeatures:
    if not campaign_id:
        raise HTTPException(status_code=400, detail="campaign_id is required")

    try:
        data = REDIS.hgetall(f"campaign:{campaign_id}:features")
    except redis.RedisError as exc:
        raise HTTPException(status_code=503, detail=f"redis unavailable: {exc}") from exc

    return CampaignFeatures(
        views=int(data.get("views", 0)),
        clicks=int(data.get("clicks", 0)),
        conversions=int(data.get("conv", 0)),
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
