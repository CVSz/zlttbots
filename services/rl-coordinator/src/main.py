import os
from typing import Any

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="RL Coordinator")
TIMEOUT = float(os.getenv("RL_COORDINATOR_TIMEOUT", "2.0"))
AGENTS = [agent.strip() for agent in os.getenv("RL_AGENTS", "rl-agent-1:8000,rl-agent-2:8000").split(",") if agent.strip()]


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    campaign_id: str = Field(min_length=1)
    candidate_campaign_ids: list[str] = Field(default_factory=list)
    features: dict[str, Any] = Field(default_factory=dict)


class UpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    campaign_id: str = Field(min_length=1)
    features: dict[str, Any] = Field(default_factory=dict)
    reward: float = Field(ge=0.0)


class AgentStatus(BaseModel):
    agent: str
    ok: bool
    detail: str | None = None


def call_agent(agent: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.post(f"http://{agent}{path}", json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        data["agent"] = agent
        return data
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"agent {agent} unavailable: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"agent {agent} returned invalid json: {exc}") from exc


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    statuses: list[dict[str, Any]] = []
    healthy = 0
    for agent in AGENTS:
        try:
            response = requests.get(f"http://{agent}/healthz", timeout=TIMEOUT)
            response.raise_for_status()
            statuses.append(AgentStatus(agent=agent, ok=True).model_dump())
            healthy += 1
        except requests.RequestException as exc:
            statuses.append(AgentStatus(agent=agent, ok=False, detail=str(exc)).model_dump())

    return {
        "status": "ok" if healthy else "degraded",
        "service": "rl-coordinator",
        "healthy_agents": healthy,
        "configured_agents": len(AGENTS),
        "agents": statuses,
    }


@app.post("/decide")
def decide(request: DecisionRequest) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    best_score = float("-inf")
    errors: list[str] = []

    for agent in AGENTS:
        try:
            candidate = call_agent(agent, "/select", request.model_dump())
        except HTTPException as exc:
            errors.append(str(exc.detail))
            continue

        score = float(candidate.get("score", float("-inf")))
        if score > best_score:
            best = candidate
            best_score = score

    if best is None:
        raise HTTPException(status_code=503, detail={"message": "no agent available", "errors": errors})

    best["evaluated_agents"] = len(AGENTS)
    return best


@app.post("/update")
def update(request: UpdateRequest) -> dict[str, Any]:
    updated_agents: list[str] = []
    errors: list[str] = []

    for agent in AGENTS:
        try:
            call_agent(agent, "/update", request.model_dump())
            updated_agents.append(agent)
        except HTTPException as exc:
            errors.append(str(exc.detail))

    if not updated_agents:
        raise HTTPException(status_code=503, detail={"message": "update failed on all agents", "errors": errors})

    return {
        "ok": True,
        "campaign_id": request.campaign_id,
        "reward": request.reward,
        "updated_agents": updated_agents,
        "errors": errors,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
