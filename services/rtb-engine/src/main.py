from pathlib import Path
import sys
from typing import Any

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from latency_bid import latency_adjusted_bid

app = FastAPI(title="RTB Engine")


class BidRequest(BaseModel):
    campaign_id: str = Field(min_length=1)
    score: float = Field(ge=0.0)
    ctr: float = Field(ge=0.0)
    cvr: float = Field(ge=0.0)
    base_bid: float = Field(gt=0.0)
    pacing_ratio: float = Field(default=1.0, ge=0.1, le=2.0)
    max_bid: float = Field(default=10.0, gt=0.0)
    latency_ms: float = Field(default=100.0, ge=0.0)


class BidResponse(BaseModel):
    campaign_id: str
    bid_price: float
    ev: float
    pacing_multiplier: float


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
    return BidResponse(
        campaign_id=request.campaign_id,
        bid_price=round(bid_price, 4),
        ev=round(ev, 8),
        pacing_multiplier=round(pacing_multiplier, 4),
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
