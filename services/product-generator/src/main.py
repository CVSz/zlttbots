import hashlib
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="AI Product Generator")
BASE_PRICE = 19.99
MARKET_CURRENCY = {"TH": "THB", "US": "USD", "EU": "EUR"}


class ProductIdea(BaseModel):
    niche: str = Field(min_length=2, max_length=120)
    market: str = Field(min_length=2, max_length=8)
    tenant_id: int = Field(ge=1)


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"status": "ok", "service": "product-generator", "supported_markets": sorted(MARKET_CURRENCY)}


@app.post("/generate")
def generate(payload: ProductIdea) -> dict[str, Any]:
    market = payload.market.upper()
    stable_id = hashlib.sha256(f"{payload.tenant_id}:{payload.niche}:{market}".encode("utf-8")).hexdigest()[:16]
    multiplier = {"TH": 0.9, "US": 1.0, "EU": 1.15}.get(market, 1.0)
    price = round(BASE_PRICE * multiplier, 2)
    return {
        "product_id": stable_id,
        "tenant_id": payload.tenant_id,
        "market": market,
        "title": f"{payload.niche.title()} Starter Kit ({market})",
        "price": price,
        "currency": MARKET_CURRENCY.get(market, "USD"),
        "landing_url": f"http://landing-service:8000/landing/{stable_id}",
        "description": f"Deterministic {payload.niche} bundle localized for {market}.",
        "guardrails": {"scraping": "disabled", "source": "deterministic-generator"},
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
