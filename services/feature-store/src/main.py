import os
from typing import Any

import redis
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Feature Store")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
REDIS = redis.Redis.from_url(REDIS_URL, decode_responses=True)


class CampaignFeatures(BaseModel):
    views: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue: float = 0.0
    spend: float = 0.0
    max_budget: float = 100.0
    daily_cap: float = 100.0
    base_bid: float = 0.1


class FeatureUpdate(BaseModel):
    views: int = Field(default=0)
    clicks: int = Field(default=0)
    conversions: int = Field(default=0)
    revenue: float = Field(default=0.0)
    spend: float | None = None
    max_budget: float | None = None
    daily_cap: float | None = None
    base_bid: float | None = None
    mode: str = Field(default="increment")


def _load_features(campaign_id: str) -> CampaignFeatures:
    try:
        data = REDIS.hgetall(f"campaign:{campaign_id}:features")
    except redis.RedisError as exc:
        raise HTTPException(status_code=503, detail=f"redis unavailable: {exc}") from exc

    return CampaignFeatures(
        views=int(data.get("views", 0)),
        clicks=int(data.get("clicks", 0)),
        conversions=int(data.get("conv", 0)),
        revenue=float(data.get("revenue", 0.0)),
        spend=float(data.get("spend", 0.0)),
        max_budget=float(data.get("max_budget", 100.0)),
        daily_cap=float(data.get("daily_cap", data.get("max_budget", 100.0))),
        base_bid=float(data.get("base_bid", 0.1)),
    )


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
    return _load_features(campaign_id)


@app.post("/features/{campaign_id}", response_model=CampaignFeatures)
def update_features(campaign_id: str, request: FeatureUpdate) -> CampaignFeatures:
    if not campaign_id:
        raise HTTPException(status_code=400, detail="campaign_id is required")

    current = _load_features(campaign_id)
    if request.mode not in {"increment", "replace"}:
        raise HTTPException(status_code=400, detail="mode must be increment or replace")

    if request.mode == "replace":
        updated = CampaignFeatures(
            views=request.views,
            clicks=request.clicks,
            conversions=request.conversions,
            revenue=request.revenue,
            spend=request.spend if request.spend is not None else current.spend,
            max_budget=request.max_budget if request.max_budget is not None else current.max_budget,
            daily_cap=request.daily_cap if request.daily_cap is not None else current.daily_cap,
            base_bid=request.base_bid if request.base_bid is not None else current.base_bid,
        )
    else:
        updated = CampaignFeatures(
            views=current.views + request.views,
            clicks=current.clicks + request.clicks,
            conversions=current.conversions + request.conversions,
            revenue=current.revenue + request.revenue,
            spend=request.spend if request.spend is not None else current.spend,
            max_budget=request.max_budget if request.max_budget is not None else current.max_budget,
            daily_cap=request.daily_cap if request.daily_cap is not None else current.daily_cap,
            base_bid=request.base_bid if request.base_bid is not None else current.base_bid,
        )

    try:
        REDIS.hset(
            f"campaign:{campaign_id}:features",
            mapping={
                "views": updated.views,
                "clicks": updated.clicks,
                "conv": updated.conversions,
                "revenue": updated.revenue,
                "spend": updated.spend,
                "max_budget": updated.max_budget,
                "daily_cap": updated.daily_cap,
                "base_bid": updated.base_bid,
            },
        )
    except redis.RedisError as exc:
        raise HTTPException(status_code=503, detail=f"redis unavailable: {exc}") from exc

    return updated


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
