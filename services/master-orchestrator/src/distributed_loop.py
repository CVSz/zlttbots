from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import requests
from fastapi import HTTPException

TIMEOUT = 10
ALLOWED_INTERNAL_HOSTS = {"feature-store", "rl-coordinator", "budget-allocator", "rtb-engine", "scaling-engine"}


def _assert_internal_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "http" or parsed.hostname not in ALLOWED_INTERNAL_HOSTS:
        raise HTTPException(status_code=400, detail="upstream url is not allowed")
    return url


def safe_call(method, url: str, **kwargs: Any) -> dict[str, Any]:
    url = _assert_internal_url(url)
    kwargs.setdefault("timeout", TIMEOUT)
    try:
        response = method(url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Upstream call failed for {url}: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"Invalid JSON response from {url}: {exc}") from exc


def run_cycle(campaign_id: str) -> dict[str, Any]:
    features = safe_call(requests.get, f"http://feature-store:8000/features/{campaign_id}")
    rl = safe_call(
        requests.post,
        "http://rl-coordinator:8000/decide",
        json={"campaign_id": campaign_id, "features": features},
    )

    current_spend = float(features.get("spend", 0.0))
    max_budget = float(features.get("max_budget", 100.0))
    daily_cap = float(features.get("daily_cap", max_budget))
    views = max(int(features.get("views", 0)), 1)
    clicks = max(int(features.get("clicks", 0)), 0)
    conversions = max(int(features.get("conversions", 0)), 0)
    ctr = clicks / views
    cvr = conversions / max(clicks, 1)
    pacing_ratio = min(2.0, max(0.1, (current_spend / daily_cap) if daily_cap else 1.0))

    budget = safe_call(
        requests.post,
        "http://budget-allocator:8000/allocate",
        json={
            "campaign_id": campaign_id,
            "score": rl["score"],
            "current_spend": current_spend,
            "max_budget": max_budget,
            "daily_cap": daily_cap,
        },
    )
    bid = safe_call(
        requests.post,
        "http://rtb-engine:8000/bid",
        json={
            "campaign_id": campaign_id,
            "score": rl["score"],
            "ctr": ctr,
            "cvr": cvr,
            "base_bid": float(features.get("base_bid", 0.1)),
            "pacing_ratio": pacing_ratio,
        },
    )
    scale = safe_call(
        requests.post,
        "http://scaling-engine:8000/scale",
        json={"campaign_id": rl["selected_campaign_id"], "score": rl["score"]},
    )

    return {"features": features, "rl": rl, "budget": budget, "bid": bid, "scale": scale}
