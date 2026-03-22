from __future__ import annotations

import os

import stripe

stripe.api_key = os.getenv("STRIPE_KEY")



def charge(amount: float, currency: str = "usd"):
    return stripe.PaymentIntent.create(amount=int(amount * 100), currency=currency)
