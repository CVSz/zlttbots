from __future__ import annotations

from pathlib import Path
from typing import Any
import sys

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from capital_engine import CapitalEngine

app = FastAPI(title="Capital Allocator")
CAPITAL_ENGINE = CapitalEngine()


class CapitalRequest(BaseModel):
    campaign_id: str = Field(min_length=1)
    tenant_id: str = Field(default="default", min_length=1)
    score: float = Field(ge=0.0)
    max_budget: float = Field(gt=0.0)
    spent: float = Field(default=0.0, ge=0.0)
    hard_cap_ratio: float = Field(default=0.5, gt=0.0, le=1.0)


class CapitalResponse(BaseModel):
    campaign_id: str
    tenant_id: str
    target: float
    delta: float
    remaining_budget: float
    capped: bool
    reinvested_capital: float
    allocations: list[float]
    observability: dict[str, Any]


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "capital-allocator",
        "prometheus_labels": {"service": "capital-allocator", "policy": "bounded"},
        "capital": round(CAPITAL_ENGINE.capital, 4),
    }


@app.post("/allocate", response_model=CapitalResponse)
def allocate(request: CapitalRequest) -> CapitalResponse:
    ratio = min(max(request.score, 0.01), request.hard_cap_ratio)
    target = round(request.max_budget * ratio, 4)
    delta = round(target - request.spent, 4)
    reinvested_capital = CAPITAL_ENGINE.reinvest([ratio])
    allocations = CAPITAL_ENGINE.allocate([ratio, max(1.0 - ratio, 1e-6)])
    return CapitalResponse(
        campaign_id=request.campaign_id,
        tenant_id=request.tenant_id,
        target=target,
        delta=delta,
        remaining_budget=round(max(0.0, request.max_budget - request.spent), 4),
        capped=ratio >= request.hard_cap_ratio,
        reinvested_capital=round(reinvested_capital, 4),
        allocations=[round(value, 4) for value in allocations],
        observability={
            "tenant_id": request.tenant_id,
            "campaign_id": request.campaign_id,
            "hard_cap_ratio": request.hard_cap_ratio,
        },
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
