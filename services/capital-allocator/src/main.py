from typing import Any

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Capital Allocator")


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
    observability: dict[str, Any]


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "capital-allocator",
        "prometheus_labels": {"service": "capital-allocator", "policy": "bounded"},
    }


@app.post("/allocate", response_model=CapitalResponse)
def allocate(request: CapitalRequest) -> CapitalResponse:
    ratio = min(max(request.score, 0.01), request.hard_cap_ratio)
    target = round(request.max_budget * ratio, 4)
    delta = round(target - request.spent, 4)
    return CapitalResponse(
        campaign_id=request.campaign_id,
        tenant_id=request.tenant_id,
        target=target,
        delta=delta,
        remaining_budget=round(max(0.0, request.max_budget - request.spent), 4),
        capped=ratio >= request.hard_cap_ratio,
        observability={
            "tenant_id": request.tenant_id,
            "campaign_id": request.campaign_id,
            "hard_cap_ratio": request.hard_cap_ratio,
        },
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
