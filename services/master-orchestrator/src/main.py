from typing import Any

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from distributed_loop import run_cycle
from economy_loop import run_economy
from federated_loop import run_global_task
from kafka_producer import emit_decision

app = FastAPI(title="Master Orchestrator")
TIMEOUT = 10


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


class Offer(BaseModel):
    id: str = Field(min_length=1)
    video_url: str = Field(min_length=1)
    caption: str = Field(min_length=1)
    landing: str = Field(min_length=1)


class CampaignDecision(BaseModel):
    offer: dict[str, Any]
    features: dict[str, Any]
    model: dict[str, Any]
    rl: dict[str, Any]
    budget: dict[str, Any]
    bid: dict[str, Any]
    scaling: dict[str, Any]
    execution: dict[str, Any]


class CampaignCycleRequest(BaseModel):
    campaign_id: str = Field(min_length=1)


class EconomyRequest(BaseModel):
    tenant_id: int = Field(ge=1)
    niche: str = Field(min_length=2)
    markets: list[str] | None = None


class FederatedTaskRequest(BaseModel):
    campaign_id: str = Field(min_length=1)
    tenant_id: str = Field(default="default", min_length=1)
    region: str = Field(default="asia", min_length=2)


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"status": "ok", "service": "master-orchestrator"}




@app.post("/run-cycle")
def run_cycle_endpoint(request: CampaignCycleRequest) -> dict[str, Any]:
    return run_cycle(request.campaign_id)


@app.post("/economy/run")
def run_economy_endpoint(request: EconomyRequest) -> dict[str, Any]:
    return run_economy(request.tenant_id, request.niche, request.markets)


@app.post("/federation/run")
def run_federated_task_endpoint(request: FederatedTaskRequest) -> dict[str, Any]:
    return run_global_task(request.campaign_id, request.tenant_id, request.region)


@app.post("/campaign/run", response_model=CampaignDecision)
def run_campaign(offer: Offer) -> CampaignDecision:
    cycle = run_cycle(offer.id)
    model = safe_call(requests.post, "http://model-service:8000/predict", json=cycle["features"])
    execution = safe_call(
        requests.post,
        "http://execution-engine:9600/publish",
        json={
            "campaign_id": offer.id,
            "video_url": offer.video_url,
            "caption": offer.caption,
            "destination_url": offer.landing,
            "target_budget": cycle["budget"]["target_budget"],
            "bid_price": cycle["bid"]["bid_price"],
        },
    )

    emit_decision(
        {
            "campaign_id": offer.id,
            "features": cycle["features"],
            "rl": cycle["rl"],
            "budget": cycle["budget"],
            "bid": cycle["bid"],
            "scale": cycle["scale"],
            "execution": execution,
        }
    )

    return CampaignDecision(
        offer=offer.model_dump(),
        features=cycle["features"],
        model=model,
        rl=cycle["rl"],
        budget=cycle["budget"],
        bid=cycle["bid"],
        scaling=cycle["scale"],
        execution=execution,
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
