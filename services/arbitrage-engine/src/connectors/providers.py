from __future__ import annotations

import os
from typing import Any, Protocol

import requests

from connectors.contracts import (
    AffiliateNetwork,
    AffiliateOrder,
    ConnectorConfig,
    ConnectorSnapshot,
    ProductCommission,
    ProviderAuth,
)


class AffiliateConnector(Protocol):
    network: AffiliateNetwork

    def fetch_snapshot(self, auth: ProviderAuth) -> ConnectorSnapshot:
        ...


class HttpAffiliateConnector:
    def __init__(self, network: AffiliateNetwork, config: ConnectorConfig) -> None:
        self.network = network
        self.config = config

    def _request(self, path: str, auth: ProviderAuth) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.config.base_url.rstrip('/')}{path}",
            headers={"Authorization": f"Bearer {auth.token}"},
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError(f"{self.network} response must be a list")
        return payload

    def fetch_snapshot(self, auth: ProviderAuth) -> ConnectorSnapshot:
        commissions_payload = self._request("/affiliate/commissions", auth)
        orders_payload = self._request("/affiliate/orders", auth)

        commissions = [
            ProductCommission(
                network=self.network,
                product_id=str(item["product_id"]),
                payout_rate=float(item["payout_rate"]),
                currency=str(item.get("currency", "USD")),
            )
            for item in commissions_payload
        ]

        orders = [
            AffiliateOrder(
                network=self.network,
                order_id=str(item["order_id"]),
                product_id=str(item["product_id"]),
                status=str(item["status"]),
                order_total=float(item["order_total"]),
                commission_value=float(item.get("commission_value", 0)),
            )
            for item in orders_payload
        ]

        return ConnectorSnapshot(source=self.network, commissions=commissions, orders=orders)


def default_connectors() -> dict[AffiliateNetwork, HttpAffiliateConnector]:
    return {
        AffiliateNetwork.TIKTOK: HttpAffiliateConnector(
            AffiliateNetwork.TIKTOK,
            ConnectorConfig(base_url=os.getenv("TIKTOK_AFFILIATE_BASE_URL", "https://api.tiktok.example")),
        ),
        AffiliateNetwork.SHOPEE: HttpAffiliateConnector(
            AffiliateNetwork.SHOPEE,
            ConnectorConfig(base_url=os.getenv("SHOPEE_AFFILIATE_BASE_URL", "https://api.shopee.example")),
        ),
        AffiliateNetwork.LAZADA: HttpAffiliateConnector(
            AffiliateNetwork.LAZADA,
            ConnectorConfig(base_url=os.getenv("LAZADA_AFFILIATE_BASE_URL", "https://api.lazada.example")),
        ),
    }
