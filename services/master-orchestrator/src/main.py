import logging
import os
from typing import Any, Literal
from urllib.parse import quote
from urllib.parse import urlparse

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from deployment_controller import (
    DeploymentCreateRequest,
    DeploymentEventRequest,
    DeploymentStore,
)
from distributed_loop import run_cycle
from economy_loop import run_economy
from federated_loop import run_global_task
from kafka_producer import emit_decision

app = FastAPI(title="Master Orchestrator")
TIMEOUT = float(os.getenv("HTTP_TIMEOUT_SECONDS", "10"))
HTTP_RETRY_TOTAL = int(os.getenv("HTTP_RETRY_TOTAL", "3"))
HTTP_RETRY_BACKOFF = float(os.getenv("HTTP_RETRY_BACKOFF", "0.5"))
logging.basicConfig(level=logging.INFO)


CLICK_TRACKER_URL = os.getenv("CLICK_TRACKER_URL", "http://click-tracker:8080")
PAYMENT_GATEWAY_URL = os.getenv("PAYMENT_GATEWAY_URL", "http://payment-gateway:8000")
FEATURE_STORE_URL = os.getenv("FEATURE_STORE_URL", "http://feature-store:8000")
MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://model-service:8000")
EXECUTION_ENGINE_URL = os.getenv("EXECUTION_ENGINE_URL", "http://execution-engine:9600")
APP_PORT = int(os.getenv("MASTER_ORCHESTRATOR_PORT", "8000"))
deployment_store = DeploymentStore()
ALLOWED_UPSTREAM_HOSTS = {
    "click-tracker",
    "payment-gateway",
    "feature-store",
    "model-service",
    "execution-engine",
    "scheduler",
}


class PaymentConfig(BaseModel):
    provider: Literal["stripe", "crypto"] = "stripe"
    amount: float = Field(gt=0)
    currency: str = Field(default="usd", min_length=3, max_length=8)
    success_url: HttpUrl
    cancel_url: HttpUrl
    wallet_address: str | None = None


class ProfitModeRequest(BaseModel):
    campaign_id: str = Field(min_length=1)
    video_url: HttpUrl
    caption: str = Field(min_length=1, max_length=2200)
    landing_url: HttpUrl
    affiliate_product_id: str | None = Field(default=None, min_length=1)
    tenant_id: str = Field(default="default", min_length=1)
    region: str = Field(default="global", min_length=2)
    market: str = Field(default="US", min_length=2, max_length=8)
    payment: PaymentConfig
    max_budget: float = Field(default=100.0, gt=0)
    daily_cap: float = Field(default=50.0, gt=0)
    base_bid: float = Field(default=0.25, gt=0)


class ProfitModeResponse(BaseModel):
    campaign_id: str
    tracked_destination_url: str
    features: dict[str, Any]
    model: dict[str, Any]
    rl: dict[str, Any]
    budget: dict[str, Any]
    bid: dict[str, Any]
    execution: dict[str, Any]
    payment: dict[str, Any]
    audit: dict[str, Any]


def safe_call(method_func, url: str, **kwargs: Any) -> dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in ALLOWED_UPSTREAM_HOSTS:
        raise HTTPException(status_code=400, detail="upstream url is not allowed")

    kwargs.setdefault("timeout", TIMEOUT)
    session = requests.Session()
    retries = Retry(
        total=HTTP_RETRY_TOTAL,
        connect=HTTP_RETRY_TOTAL,
        read=HTTP_RETRY_TOTAL,
        status=HTTP_RETRY_TOTAL,
        backoff_factor=HTTP_RETRY_BACKOFF,
        status_forcelist=[502, 503, 504],
        allowed_methods={"DELETE", "GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH"},
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    method_name = getattr(method_func, "__name__", "").lower()
    if method_name not in {"get", "post", "put", "patch", "delete", "head", "options"}:
        raise HTTPException(status_code=500, detail=f"Unsupported HTTP method callable: {method_func}")
    try:
        response = getattr(session, method_name)(url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Upstream call failed: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"Invalid JSON response from upstream: {exc}") from exc


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


@app.post("/deployments")
def create_deployment(payload: DeploymentCreateRequest) -> dict[str, Any]:
    deployment = deployment_store.create(payload)
    emit_decision(
        {
            "event_type": "deploy.requested",
            "deployment_id": deployment.deployment_id,
            "project_id": deployment.project_id,
            "environment": deployment.environment,
            "state": deployment.state,
            "created_at": deployment.created_at,
        }
    )
    return deployment.model_dump()


@app.get("/deployments/{deployment_id}")
def get_deployment(deployment_id: str) -> dict[str, Any]:
    try:
        deployment = deployment_store.get(deployment_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="deployment not found") from exc
    return deployment.model_dump()


@app.post("/deployments/events")
def handle_deployment_event(payload: DeploymentEventRequest) -> dict[str, Any]:
    try:
        deployment = deployment_store.apply_event(payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="deployment not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    emit_decision(
        {
            "event_type": payload.event_type,
            "deployment_id": deployment.deployment_id,
            "project_id": deployment.project_id,
            "environment": deployment.environment,
            "state": deployment.state,
            "updated_at": deployment.updated_at,
            "source": payload.source,
        }
    )
    return deployment.model_dump()




@app.post("/run-cycle")
def run_cycle_endpoint(request: CampaignCycleRequest) -> dict[str, Any]:
    return run_cycle(request.campaign_id)


@app.post("/economy/run")
def run_economy_endpoint(request: EconomyRequest) -> dict[str, Any]:
    return run_economy(request.tenant_id, request.niche, request.markets)


@app.post("/federation/run")
def run_federated_task_endpoint(request: FederatedTaskRequest) -> dict[str, Any]:
    return run_global_task(request.campaign_id, request.tenant_id, request.region)


def build_tracked_destination(campaign_id: str, landing_url: str, affiliate_product_id: str | None = None) -> str:
    if affiliate_product_id:
        return f"{CLICK_TRACKER_URL}/go/{campaign_id}/{quote(affiliate_product_id)}"
    return f"{CLICK_TRACKER_URL}/r/{campaign_id}?to={quote(landing_url, safe='')}"


def create_checkout(request: ProfitModeRequest, tracked_destination_url: str) -> dict[str, Any]:
    payload = {
        "provider": request.payment.provider,
        "campaign_id": request.campaign_id,
        "amount": request.payment.amount,
        "currency": request.payment.currency.lower(),
        "success_url": str(request.payment.success_url),
        "cancel_url": str(request.payment.cancel_url),
        "wallet_address": request.payment.wallet_address,
        "metadata": {
            "campaign_id": request.campaign_id,
            "tenant_id": request.tenant_id,
            "market": request.market,
            "tracked_destination_url": tracked_destination_url,
        },
    }
    return safe_call(requests.post, f"{PAYMENT_GATEWAY_URL}/checkout", json=payload)


@app.post("/campaign/run", response_model=CampaignDecision)
def run_campaign(offer: Offer) -> CampaignDecision:
    cycle = run_cycle(offer.id)
    model = safe_call(requests.post, f"{MODEL_SERVICE_URL}/predict", json=cycle["features"])
    execution = safe_call(
        requests.post,
        f"{EXECUTION_ENGINE_URL}/publish",
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


@app.post("/profit-mode/activate", response_model=ProfitModeResponse)
def activate_profit_mode(request: ProfitModeRequest) -> ProfitModeResponse:
    safe_call(
        requests.post,
        f"{FEATURE_STORE_URL}/features/{request.campaign_id}",
        json={
            "max_budget": request.max_budget,
            "daily_cap": request.daily_cap,
            "base_bid": request.base_bid,
            "mode": "increment",
        },
    )
    cycle = run_cycle(request.campaign_id)
    model = safe_call(requests.post, f"{MODEL_SERVICE_URL}/predict", json=cycle["features"])
    tracked_destination_url = build_tracked_destination(
        request.campaign_id,
        str(request.landing_url),
        request.affiliate_product_id,
    )
    execution = safe_call(
        requests.post,
        f"{EXECUTION_ENGINE_URL}/publish",
        json={
            "campaign_id": request.campaign_id,
            "video_url": str(request.video_url),
            "caption": request.caption,
            "destination_url": tracked_destination_url,
        },
    )
    payment = create_checkout(request, tracked_destination_url)
    audit = {
        "tenant_id": request.tenant_id,
        "region": request.region,
        "market": request.market,
        "payment_provider": request.payment.provider,
        "tracked_destination_url": tracked_destination_url,
        "profit_mode": True,
    }
    emit_decision(
        {
            "campaign_id": request.campaign_id,
            "features": cycle["features"],
            "model": model,
            "rl": cycle["rl"],
            "budget": cycle["budget"],
            "bid": cycle["bid"],
            "execution": execution,
            "payment": payment,
            "audit": audit,
        }
    )
    return ProfitModeResponse(
        campaign_id=request.campaign_id,
        tracked_destination_url=tracked_destination_url,
        features=cycle["features"],
        model=model,
        rl=cycle["rl"],
        budget=cycle["budget"],
        bid=cycle["bid"],
        execution=execution,
        payment=payment,
        audit=audit,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)
