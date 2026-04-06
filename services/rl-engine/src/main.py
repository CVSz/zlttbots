import os
from pathlib import Path
from typing import Any

import numpy as np
import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from linucb import LinUCB
from store import load_state, log_decision, save_state

app = FastAPI(title="RL Engine (LinUCB)")
STATE_KEY = os.getenv("RL_STATE_KEY", "rl:linucb")
DEFAULT_ALPHA = float(os.getenv("RL_ALPHA", "1.0"))
DEFAULT_LAMBDA = float(os.getenv("RL_LAMBDA", "1.0"))
MODEL_PATH = Path(os.getenv("RL_POLICY_MODEL_PATH", "/models/policy.pt"))


class Features(BaseModel):
    model_config = ConfigDict(extra="ignore")

    views: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    conversions: int = Field(default=0, ge=0)


class SelectionRequest(BaseModel):
    campaign_id: str = Field(min_length=1)
    candidate_campaign_ids: list[str] = Field(default_factory=list)
    features: Features


class UpdateRequest(BaseModel):
    campaign_id: str = Field(min_length=1)
    features: Features
    reward: float = Field(ge=0.0)


class RLDecision(BaseModel):
    campaign_id: str
    selected_campaign_id: str
    score: float
    arms: list[str]


class UpdateResponse(BaseModel):
    ok: bool
    campaign_id: str
    reward: float


def to_vector(features: Features) -> np.ndarray:
    ctr = (features.clicks / features.views) if features.views else 0.0
    cvr = (features.conversions / features.clicks) if features.clicks else 0.0
    return np.array([[ctr], [cvr]], dtype=np.float64)


def load_agent(arms: list[str]) -> LinUCB:
    agent = LinUCB(arms=arms, d=2, alpha=DEFAULT_ALPHA, lam=DEFAULT_LAMBDA)
    stored = load_state(STATE_KEY)
    if not stored:
        return agent

    for arm in stored.get("arms", []):
        agent.add_arm(arm)
        agent.A[arm] = np.array(stored["A"][arm], dtype=np.float64)
        agent.b[arm] = np.array(stored["b"][arm], dtype=np.float64)
    return agent


def persist_agent(agent: LinUCB) -> None:
    payload = {
        "arms": agent.arms,
        "A": {arm: agent.A[arm].tolist() for arm in agent.arms},
        "b": {arm: agent.b[arm].tolist() for arm in agent.arms},
    }
    save_state(STATE_KEY, payload)


def load_policy_model():
    if not MODEL_PATH.exists():
        return None

    try:
        from policy_model import Policy

        return Policy.load(MODEL_PATH)
    except Exception:
        return None


def score_with_policy(features: Features) -> float | None:
    policy = load_policy_model()
    if policy is None:
        return None

    vector = np.array(
        [[(features.clicks / features.views) if features.views else 0.0, (features.conversions / features.clicks) if features.clicks else 0.0]],
        dtype=np.float64,
    )
    probabilities = policy(vector)
    return float(probabilities[0][1])


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    try:
        saved = load_state(STATE_KEY)
        redis_ok = True
    except redis.RedisError:
        saved = None
        redis_ok = False
    return {
        "status": "ok" if redis_ok else "degraded",
        "service": "rl-engine",
        "checks": {"redis": redis_ok},
        "arms": len(saved.get("arms", [])) if saved else 0,
    }


@app.post("/select", response_model=RLDecision)
def select(request: SelectionRequest) -> RLDecision:
    arms = list(dict.fromkeys([request.campaign_id, *request.candidate_campaign_ids]))
    try:
        agent = load_agent(arms)
        vector = to_vector(request.features)
        selected_campaign_id, score = agent.select(vector)
        policy_score = score_with_policy(request.features)
        if policy_score is not None:
            score = policy_score
            selected_campaign_id = request.campaign_id
        persist_agent(agent)
        log_decision(
            campaign_id=request.campaign_id,
            selected_campaign_id=selected_campaign_id,
            score=score,
            features=request.features.model_dump(),
        )
    except redis.RedisError as exc:
        raise HTTPException(status_code=503, detail=f"redis unavailable: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"selection failed: {exc}") from exc

    return RLDecision(
        campaign_id=request.campaign_id,
        selected_campaign_id=selected_campaign_id,
        score=score,
        arms=agent.arms,
    )


@app.post("/update", response_model=UpdateResponse)
def update(request: UpdateRequest) -> UpdateResponse:
    try:
        agent = load_agent([request.campaign_id])
        agent.update(request.campaign_id, to_vector(request.features), request.reward)
        persist_agent(agent)
    except redis.RedisError as exc:
        raise HTTPException(status_code=503, detail=f"redis unavailable: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"update failed: {exc}") from exc

    return UpdateResponse(ok=True, campaign_id=request.campaign_id, reward=request.reward)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
