import os
from typing import Any

try:
    import redis
except ModuleNotFoundError:  # pragma: no cover - dependency optional in unit tests
    redis = None
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="Feature Store")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
class _InMemoryRedis:
    def __init__(self) -> None:
        self._db: dict[str, dict[str, str]] = {}

    def hgetall(self, key: str) -> dict[str, str]:
        return dict(self._db.get(key, {}))

    def hset(self, key: str, mapping: dict[str, Any]) -> None:
        self._db[key] = {k: str(v) for k, v in mapping.items()}

    def ping(self) -> bool:
        return True


class _RedisError(Exception):
    pass


if redis is None:
    class _RedisNamespace:  # pragma: no cover - used only when redis package is missing
        RedisError = _RedisError

    redis = _RedisNamespace()
    REDIS = _InMemoryRedis()
else:
    REDIS = redis.Redis.from_url(REDIS_URL, decode_responses=True)


class CampaignFeatures(BaseModel):
    views: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    conversions: int = Field(default=0, ge=0)
    revenue: float = Field(default=0.0, ge=0.0)
    spend: float = Field(default=0.0, ge=0.0)
    max_budget: float = Field(default=100.0, ge=0.0)
    daily_cap: float = Field(default=100.0, ge=0.0)
    base_bid: float = Field(default=0.1, ge=0.0)

    @field_validator("daily_cap")
    @classmethod
    def validate_daily_cap(cls, daily_cap: float, info):
        max_budget = info.data.get("max_budget")
        if max_budget is not None and daily_cap > max_budget:
            raise ValueError("daily_cap must be less than or equal to max_budget")
        return daily_cap


class FeatureUpdate(BaseModel):
    views: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    conversions: int = Field(default=0, ge=0)
    revenue: float = Field(default=0.0, ge=0.0)
    spend: float | None = Field(default=None, ge=0.0)
    max_budget: float | None = Field(default=None, ge=0.0)
    daily_cap: float | None = Field(default=None, ge=0.0)
    base_bid: float | None = Field(default=None, ge=0.0)
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


def _save_features(campaign_id: str, features: CampaignFeatures) -> None:
    try:
        REDIS.hset(
            f"campaign:{campaign_id}:features",
            mapping={
                "views": features.views,
                "clicks": features.clicks,
                "conv": features.conversions,
                "revenue": features.revenue,
                "spend": features.spend,
                "max_budget": features.max_budget,
                "daily_cap": features.daily_cap,
                "base_bid": features.base_bid,
            },
        )
    except redis.RedisError as exc:
        raise HTTPException(status_code=503, detail=f"redis unavailable: {exc}") from exc


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

    _save_features(campaign_id, updated)
    return updated


@app.put("/features/{campaign_id}", response_model=CampaignFeatures)
def replace_all_features(campaign_id: str, request: CampaignFeatures) -> CampaignFeatures:
    if not campaign_id:
        raise HTTPException(status_code=400, detail="campaign_id is required")

    _save_features(campaign_id, request)
    return request


@app.put("/features", response_model=dict[str, CampaignFeatures])
def replace_all_campaign_features(request: dict[str, CampaignFeatures]) -> dict[str, CampaignFeatures]:
    if not request:
        raise HTTPException(status_code=400, detail="at least one campaign payload is required")

    for campaign_id, payload in request.items():
        if not campaign_id:
            raise HTTPException(status_code=400, detail="campaign_id is required")
        _save_features(campaign_id, payload)

    return request


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
