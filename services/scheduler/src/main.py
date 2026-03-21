import base64
import binascii
import hashlib
import hmac
import json
import os
from typing import Any

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Global Scheduler")
FEDERATION_URL = os.getenv("FEDERATION_URL", "http://federation:8000")
FEDERATION_SECRET = os.getenv("FEDERATION_SECRET", "change-me")
TIMEOUT = float(os.getenv("SCHEDULER_TIMEOUT", "3.0"))


class Task(BaseModel):
    task_id: str = Field(min_length=1)
    required_capacity: int = Field(ge=1)
    region: str = Field(min_length=2)
    tenant_id: str = Field(default="default", min_length=1)
    max_latency_ms: int = Field(default=250, ge=1)
    task_token: str = Field(min_length=16)


class Assignment(BaseModel):
    assigned: str | None
    candidate_count: int
    policy: str
    reason: str | None = None
    observability: dict[str, Any]


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    federation_ok = False
    try:
        response = requests.get(f"{FEDERATION_URL}/healthz", timeout=TIMEOUT)
        federation_ok = response.ok
    except requests.RequestException:
        federation_ok = False
    return {
        "status": "ok" if federation_ok else "degraded",
        "service": "scheduler",
        "checks": {"federation": federation_ok},
        "prometheus_labels": {"service": "scheduler", "policy": "capacity-latency-aware"},
    }


def fetch_nodes() -> list[dict[str, Any]]:
    try:
        response = requests.get(f"{FEDERATION_URL}/nodes", timeout=TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise HTTPException(status_code=503, detail=f"federation unavailable: {exc}") from exc
    return payload.get("nodes", [])


def decode_task_token(token: str) -> dict[str, Any]:
    try:
        payload_b64, signature_b64 = token.split('.', 1)
        payload = base64.urlsafe_b64decode(payload_b64.encode('utf-8'))
        actual_signature = base64.urlsafe_b64decode(signature_b64.encode('utf-8'))
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(status_code=401, detail=f"invalid task token format: {exc}") from exc

    expected_signature = hmac.new(FEDERATION_SECRET.encode('utf-8'), payload, hashlib.sha256).digest()
    if not hmac.compare_digest(actual_signature, expected_signature):
        raise HTTPException(status_code=401, detail='invalid task token signature')

    try:
        claims = json.loads(payload.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=401, detail=f"invalid task token payload: {exc}") from exc
    return claims


def verify_task_token(task: Task) -> dict[str, Any]:
    claims = decode_task_token(task.task_token)
    if claims.get('tenant_id') != task.tenant_id:
        raise HTTPException(status_code=403, detail='tenant mismatch in task token')
    return claims


@app.post("/assign", response_model=Assignment)
def assign(task: Task) -> Assignment:
    verify_task_token(task)
    nodes = fetch_nodes()
    tenant_nodes = [node for node in nodes if node.get("tenant_id") == task.tenant_id]
    candidates = [node for node in tenant_nodes if node.get("capacity", 0) >= task.required_capacity]
    if not candidates:
        return Assignment(
            assigned=None,
            candidate_count=0,
            policy="capacity-latency-aware",
            reason="no nodes satisfy tenant and capacity constraints",
            observability={"tenant_id": task.tenant_id, "region": task.region, "task_id": task.task_id},
        )

    def score(node: dict[str, Any]) -> tuple[int, int, str]:
        latency_penalty = 0 if node.get("region") == task.region else 1
        available_capacity = int(node.get("capacity", 0))
        return (latency_penalty, -available_capacity, node.get("node_id", ""))

    selected = sorted(candidates, key=score)[0]
    return Assignment(
        assigned=selected.get("node_id"),
        candidate_count=len(candidates),
        policy="capacity-latency-aware",
        observability={
            "tenant_id": task.tenant_id,
            "region": task.region,
            "selected_node": selected.get("node_id"),
            "labels": selected.get("labels", {}),
        },
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
