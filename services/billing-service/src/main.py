from decimal import Decimal
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Billing Service")
PLAN_RATES = {"free": Decimal("0.00"), "growth": Decimal("0.01"), "scale": Decimal("0.02")}


class UsageChargeRequest(BaseModel):
    tenant_id: int = Field(ge=1)
    usage: int = Field(ge=0)
    plan: str = Field(default="free", min_length=2, max_length=50)


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"status": "ok", "service": "billing-service", "plans": sorted(PLAN_RATES)}


@app.post("/charge")
def charge(payload: UsageChargeRequest) -> dict[str, Any]:
    unit_price = PLAN_RATES.get(payload.plan, PLAN_RATES["growth"])
    cost = (Decimal(payload.usage) * unit_price).quantize(Decimal("0.01"))
    return {
        "tenant_id": payload.tenant_id,
        "plan": payload.plan,
        "usage": payload.usage,
        "unit_price": float(unit_price),
        "cost": float(cost),
        "currency": "USD",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
