from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

REPO_ROOT = CURRENT_DIR.parents[2]
RL_TRAINER_SRC = REPO_ROOT / "services" / "rl-trainer" / "src"
ANALYTICS_DIR = REPO_ROOT / "services" / "analytics"
for extra_path in (RL_TRAINER_SRC, ANALYTICS_DIR):
    if str(extra_path) not in sys.path:
        sys.path.insert(0, str(extra_path))

from causal_rl import doubly_robust
from hierarchical_rl import HierarchicalRL
from latency_bid import latency_adjusted_bid
from long_term_reward import long_term_reward
from ltv_model import LTVModel

app = FastAPI(title="RTB Engine")
hrl = HierarchicalRL()
ltv_model = LTVModel()


class BidRequest(BaseModel):
    campaign_id: str = Field(min_length=1)
    score: float = Field(ge=0.0)
    ctr: float = Field(ge=0.0)
    cvr: float = Field(ge=0.0)
    base_bid: float = Field(gt=0.0)
    pacing_ratio: float = Field(default=1.0, ge=0.1, le=2.0)
    max_bid: float = Field(default=10.0, gt=0.0)
    latency_ms: float = Field(default=100.0, ge=0.0)
    revenue: float = Field(default=0.0)
    propensity: float = Field(default=0.5, gt=0.0)
    model_pred: float = Field(default=0.1)


class BidResponse(BaseModel):
    campaign_id: str
    bid_price: float
    ev: float
    pacing_multiplier: float
    hierarchical_decisions: dict[str, int]
    ltv: float
    long_term_reward: float
    counterfactual_reward: float


class OpenRTBImpression(BaseModel):
    id: str = Field(min_length=1)


class OpenRTBDevice(BaseModel):
    ua: str | None = None
    ip: str | None = None


class OpenRTBUser(BaseModel):
    id: str | None = None


class OpenRTBBidRequest(BaseModel):
    id: str = Field(min_length=1)
    imp: list[OpenRTBImpression] = Field(min_length=1)
    device: OpenRTBDevice = Field(default_factory=OpenRTBDevice)
    user: OpenRTBUser = Field(default_factory=OpenRTBUser)


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"status": "ok", "service": "rtb-engine"}


@app.post("/bid", response_model=BidResponse)
def bid(request: BidRequest) -> BidResponse:
    ev = request.ctr * request.cvr * request.score
    pacing_multiplier = 0.5 + (request.pacing_ratio / 2)
    bid_price = latency_adjusted_bid(
        base_bid=request.base_bid,
        score=request.score,
        latency_ms=request.latency_ms,
        pacing_multiplier=pacing_multiplier,
        ctr=request.ctr,
        cvr=request.cvr,
        max_bid=request.max_bid,
    )

    features = [request.ctr, request.cvr]
    decisions = hrl.select(features)
    ltv = ltv_model.predict(features)
    shaped_reward = long_term_reward(short_term=request.revenue - bid_price, ltv=ltv)
    counterfactual_reward = doubly_robust(shaped_reward, request.propensity, request.model_pred)
    hrl.update(features, counterfactual_reward)

    return BidResponse(
        campaign_id=request.campaign_id,
        bid_price=round(bid_price, 4),
        ev=round(ev, 8),
        pacing_multiplier=round(pacing_multiplier, 4),
        hierarchical_decisions=decisions,
        ltv=round(ltv, 6),
        long_term_reward=round(shaped_reward, 6),
        counterfactual_reward=round(counterfactual_reward, 6),
    )


@app.post("/openrtb/bid")
def openrtb_bid(request: OpenRTBBidRequest) -> dict[str, Any]:
    first_imp = request.imp[0]
    return {
        "id": request.id,
        "seatbid": [
            {
                "bid": [
                    {
                        "impid": first_imp.id,
                        "price": 0.05,
                        "adm": "<html>Ad</html>",
                    }
                ]
            }
        ],
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
