from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from typing import Any

import requests
from fastapi import HTTPException

TIMEOUT = float(os.getenv("FEDERATED_LOOP_TIMEOUT", "5.0"))
FEDERATION_SECRET = os.getenv("FEDERATION_SECRET", "change-me")
DEFAULT_REGION = os.getenv("FEDERATED_DEFAULT_REGION", "asia")
DEFAULT_TENANT = os.getenv("FEDERATED_DEFAULT_TENANT", "default")
DEFAULT_MAX_BUDGET = float(os.getenv("FEDERATED_MAX_BUDGET", "100"))


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


def build_task_token(campaign_id: str, tenant_id: str, region: str) -> str:
    payload = json.dumps(
        {"campaign_id": campaign_id, "tenant_id": tenant_id, "region": region},
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    signature = hmac.new(FEDERATION_SECRET.encode("utf-8"), payload, hashlib.sha256).digest()
    return f"{base64.urlsafe_b64encode(payload).decode('utf-8')}.{base64.urlsafe_b64encode(signature).decode('utf-8')}"


def run_global_task(campaign_id: str, tenant_id: str = DEFAULT_TENANT, region: str = DEFAULT_REGION) -> dict[str, Any]:
    features = safe_call(requests.get, f"http://feature-store:8000/features/{campaign_id}")
    rl = safe_call(
        requests.post,
        "http://rl-coordinator:8000/decide",
        json={"campaign_id": campaign_id, "features": features},
    )
    capital = safe_call(
        requests.post,
        "http://capital-allocator:8000/allocate",
        json={
            "campaign_id": campaign_id,
            "tenant_id": tenant_id,
            "score": rl["score"],
            "max_budget": float(features.get("max_budget", DEFAULT_MAX_BUDGET)),
            "spent": float(features.get("spend", 0.0)),
        },
    )
    scheduler = safe_call(
        requests.post,
        "http://scheduler:8000/assign",
        json={
            "task_id": campaign_id,
            "required_capacity": 1,
            "region": region,
            "tenant_id": tenant_id,
            "task_token": build_task_token(campaign_id, tenant_id, region),
        },
    )
    return {"features": features, "rl": rl, "capital": capital, "node": scheduler}
