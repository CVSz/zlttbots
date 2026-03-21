from typing import Any

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Master Orchestrator")
TIMEOUT = 10


def decide_and_scale(campaign_id: str, features: dict[str, Any]) -> dict[str, Any]:
    selection = safe_call(
        requests.post,
        "http://rl-engine:8000/select",
        json={"campaign_id": campaign_id, "features": features},
    )
    scaling = safe_call(
        requests.post,
        "http://scaling-engine:8000/scale",
        json={"campaign_id": selection["selected_campaign_id"], "score": selection["score"]},
    )
    return {"rl": selection, "scaling": scaling}


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
    scaling: dict[str, Any]
    execution: dict[str, Any]


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
    return {"status": "ok", "service": "master-orchestrator"}


@app.post("/campaign/run", response_model=CampaignDecision)
def run_campaign(offer: Offer) -> CampaignDecision:
    metrics = safe_call(requests.get, f"http://feature-store:8000/features/{offer.id}")
    model = safe_call(requests.post, "http://model-service:8000/predict", json=metrics)
    rl_result = decide_and_scale(offer.id, metrics)
    execution = safe_call(
        requests.post,
        "http://execution-engine:9600/publish",
        json={
            "campaign_id": offer.id,
            "video_url": offer.video_url,
            "caption": offer.caption,
            "destination_url": offer.landing,
        },
    )

    return CampaignDecision(
        offer=offer.model_dump(),
        features=metrics,
        model=model,
        rl=rl_result["rl"],
        scaling=rl_result["scaling"],
        execution=execution,
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
