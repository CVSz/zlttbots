from __future__ import annotations

from typing import Any

import requests
from fastapi import HTTPException

from distributed_loop import run_cycle

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


def run_economy(tenant_id: int, niche: str, markets: list[str] | None = None) -> dict[str, Any]:
    launch = safe_call(
        requests.post,
        "http://market-orchestrator:8000/launch",
        json={"tenant_id": tenant_id, "niche": niche, "markets": markets},
    )

    outputs: list[dict[str, Any]] = []

    for item in launch["launch"]:
        product = item["product"]
        pid = product["product_id"]
        cycle = run_cycle(pid)
        billing = safe_call(
            requests.post,
            "http://billing-service:8000/charge",
            json={"tenant_id": tenant_id, "plan": "growth", "usage": max(int(cycle["features"].get("views", 0)), 1)},
        )

        outputs.append({
            "product": item,
            "cycle": cycle,
            "billing": billing,
        })

    return {"tenant_id": tenant_id, "economy": outputs}
