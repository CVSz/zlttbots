from __future__ import annotations

from connectors.contracts import AffiliateNetwork, ProviderAuth
from connectors.providers import AffiliateConnector, default_connectors


class UnifiedAffiliateClient:
    def __init__(self, connectors: dict[AffiliateNetwork, AffiliateConnector] | None = None) -> None:
        self._connectors = connectors or default_connectors()

    def fetch_network_snapshot(self, network: AffiliateNetwork, auth_token: str):
        connector = self._connectors[network]
        return connector.fetch_snapshot(ProviderAuth(token=auth_token))
