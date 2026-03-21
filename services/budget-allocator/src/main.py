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

from bandit import UCBBandit

app = FastAPI(title="Budget Allocator")
BANDIT = UCBBandit(n_arms=3)


class BudgetRequest(BaseModel):
    campaign_id: str = Field(min_length=1)
    score: float = Field(ge=0.0)
    current_spend: float = Field(default=0.0, ge=0.0)
    max_budget: float = Field(gt=0.0)
    daily_cap: float | None = Field(default=None, gt=0.0)
    min_step: float = Field(default=1.0, gt=0.0)
    max_step: float = Field(default=25.0, gt=0.0)


class BudgetResponse(BaseModel):
    campaign_id: str
    target_budget: float
    adjustment: float
    available_budget: float
    capped: bool
    selected_arm: int


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"status": "ok", "service": "budget-allocator", "bandit_arms": len(BANDIT.values)}


@app.post("/allocate", response_model=BudgetResponse)
def allocate(request: BudgetRequest) -> BudgetResponse:
    ratio = min(max(request.score, 0.01), 1.0)
    cap = min(request.max_budget, request.daily_cap) if request.daily_cap is not None else request.max_budget
    target = cap * ratio
    raw_delta = target - request.current_spend
    bounded_delta = max(-request.max_step, min(raw_delta, request.max_step))
    if 0 < abs(bounded_delta) < request.min_step:
        bounded_delta = request.min_step if bounded_delta > 0 else -request.min_step

    selected_arm = BANDIT.select()
    adjusted_target = max(0.0, min(cap, request.current_spend + bounded_delta))
    adjustment = round(adjusted_target - request.current_spend, 4)
    BANDIT.update(selected_arm, reward=ratio)

    return BudgetResponse(
        campaign_id=request.campaign_id,
        target_budget=round(adjusted_target, 4),
        adjustment=adjustment,
        available_budget=round(max(0.0, cap - request.current_spend), 4),
        capped=adjusted_target >= cap,
        selected_arm=selected_arm,
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
