from __future__ import annotations

import hashlib
import os
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from .adapter import send
from .audit import log

app = FastAPI(title="Payment Gateway")
STRIPE_ENDPOINT = os.getenv("PAYMENT_STRIPE_ENDPOINT", "https://payments.example/stripe")
CRYPTO_ENDPOINT = os.getenv("PAYMENT_CRYPTO_ENDPOINT", "https://payments.example/crypto")


class CheckoutRequest(BaseModel):
    provider: Literal["stripe", "crypto"]
    campaign_id: str = Field(min_length=1)
    amount: float = Field(gt=0)
    currency: str = Field(default="usd", min_length=3, max_length=8)
    success_url: HttpUrl
    cancel_url: HttpUrl
    wallet_address: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "payment-gateway"}


@app.post("/checkout")
def checkout(request: CheckoutRequest) -> dict[str, Any]:
    endpoint = STRIPE_ENDPOINT if request.provider == "stripe" else CRYPTO_ENDPOINT
    payload = request.model_dump(mode="json")
    if request.provider == "crypto" and not request.wallet_address:
        invoice_id = hashlib.sha256(f"{request.campaign_id}:{request.amount}:{request.currency}".encode("utf-8")).hexdigest()[:16]
        response = {
            "status": "pending",
            "provider": "crypto",
            "invoice_id": invoice_id,
            "pay_to_address": f"wallet://{invoice_id}",
            "amount": request.amount,
            "currency": request.currency.lower(),
        }
        log("payment_checkout_created", response)
        return response

    response = send(endpoint, payload)
    if response.get("status") in {"failed", "circuit_open"}:
        raise HTTPException(status_code=502, detail=response)
    log("payment_checkout_created", {"campaign_id": request.campaign_id, "provider": request.provider})
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
