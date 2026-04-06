import os
from typing import Any

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Market Orchestrator")
SUPPORTED_MARKETS = [market.strip().upper() for market in os.getenv("SUPPORTED_MARKETS", "TH,US,EU").split(",") if market.strip()]
TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "5"))


class LaunchRequest(BaseModel):
    niche: str = Field(min_length=2, max_length=120)
    tenant_id: int = Field(ge=1)
    markets: list[str] | None = None


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"status": "ok", "service": "market-orchestrator", "supported_markets": SUPPORTED_MARKETS}


@app.post("/launch")
def launch(payload: LaunchRequest) -> dict[str, Any]:
    markets = [market.upper() for market in (payload.markets or SUPPORTED_MARKETS)]
    invalid_markets = [market for market in markets if market not in SUPPORTED_MARKETS]
    if invalid_markets:
        raise HTTPException(status_code=400, detail=f"unsupported markets: {', '.join(invalid_markets)}")

    results: list[dict[str, Any]] = []
    for market in markets:
        try:
            response = requests.post(
                "http://product-generator:8000/generate",
                json={"niche": payload.niche, "market": market, "tenant_id": payload.tenant_id},
                timeout=TIMEOUT,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise HTTPException(status_code=502, detail=f"product-generator unavailable for {market}: {exc}") from exc

        results.append({"market": market, "product": response.json()})

    return {"tenant_id": payload.tenant_id, "launch": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
