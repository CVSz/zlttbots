from typing import Any

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Reward Collector")
TIMEOUT = 10


class RewardEvent(BaseModel):
    campaign_id: str = Field(min_length=1)
    revenue: float = Field(default=0.0, ge=0.0)
    conversions: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    views: int = Field(default=0, ge=0)


class RewardResponse(BaseModel):
    ok: bool
    campaign_id: str
    reward: float


def safe_call(method, url: str, **kwargs: Any) -> dict[str, Any]:
    kwargs.setdefault("timeout", TIMEOUT)
    try:
        response = method(url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Upstream call failed for {url}: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"Invalid JSON response from {url}: {exc}") from exc


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"status": "ok", "service": "reward-collector"}


@app.post("/reward", response_model=RewardResponse)
def reward(event: RewardEvent) -> RewardResponse:
    ctr = (event.clicks / event.views) if event.views else 0.0
    cvr = (event.conversions / event.clicks) if event.clicks else 0.0
    reward_value = round((0.5 * ctr) + (0.5 * cvr) + (event.revenue * 0.01), 6)

    features = safe_call(requests.get, f"http://feature-store:8000/features/{event.campaign_id}")
    safe_call(
        requests.post,
        "http://rl-engine:8000/update",
        json={"campaign_id": event.campaign_id, "features": features, "reward": reward_value},
    )
    return RewardResponse(ok=True, campaign_id=event.campaign_id, reward=reward_value)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
