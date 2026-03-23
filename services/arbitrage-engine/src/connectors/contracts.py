from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class AffiliateNetwork(str, Enum):
    TIKTOK = "tiktok"
    SHOPEE = "shopee"
    LAZADA = "lazada"


class ProviderAuth(BaseModel):
    token: str = Field(min_length=16)


class ProductCommission(BaseModel):
    network: AffiliateNetwork
    product_id: str = Field(min_length=1, max_length=128)
    payout_rate: float = Field(ge=0, le=1)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class AffiliateOrder(BaseModel):
    network: AffiliateNetwork
    order_id: str = Field(min_length=1, max_length=128)
    product_id: str = Field(min_length=1, max_length=128)
    status: Literal["pending", "approved", "cancelled"]
    order_total: float = Field(ge=0)
    commission_value: float = Field(ge=0)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConnectorConfig(BaseModel):
    base_url: HttpUrl
    timeout_seconds: float = Field(default=5.0, ge=0.1, le=30)


class ConnectorSnapshot(BaseModel):
    commissions: list[ProductCommission]
    orders: list[AffiliateOrder]
    source: AffiliateNetwork
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
