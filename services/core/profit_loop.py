from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol

from services.analytics.roi import ROIEngine
from services.analytics.unit_economics import UnitEconomics


class CampaignAPI(Protocol):
    def create_campaign(self, payload: dict[str, Any]) -> str: ...

    def pause_campaign(self, campaign_id: str) -> None: ...

    def scale_campaign(self, campaign_id: str, factor: int) -> None: ...


@dataclass(frozen=True)
class ProfitDecision:
    campaign_id: str
    roi: Decimal
    action: str


class UnitEconomicsProvider(Protocol):
    def snapshot(self, campaign_id: str) -> UnitEconomics: ...


class ProfitLoop:
    def __init__(
        self,
        roi_engine: ROIEngine,
        api: CampaignAPI,
        economics_provider: UnitEconomicsProvider | None = None,
        roi_threshold: Decimal | None = None,
    ) -> None:
        self._roi_engine = roi_engine
        self._api = api
        self._economics_provider = economics_provider
        self._roi_threshold = roi_threshold or Decimal(os.getenv("ROI_THRESHOLD", "1.2"))

    def launch(self, payload: dict[str, Any]) -> str:
        if not payload:
            raise ValueError("campaign payload is required")
        return self._api.create_campaign(payload)

    def run_once(self, campaign_id: str) -> ProfitDecision:
        if os.getenv("PROFIT_GLOBAL_KILL_SWITCH", "false").lower() == "true":
            return ProfitDecision(campaign_id=campaign_id, roi=Decimal("0"), action="halt")

        if self._economics_provider is not None:
            economics = self._economics_provider.snapshot(campaign_id)
            if economics.profit < Decimal("0"):
                self._api.pause_campaign(economics.campaign_id)
                return ProfitDecision(campaign_id=economics.campaign_id, roi=economics.roas, action="stop_loss")

        result = self._roi_engine.evaluate(campaign_id)
        if result.roi >= self._roi_threshold:
            self._api.scale_campaign(result.campaign_id, factor=2)
            return ProfitDecision(campaign_id=result.campaign_id, roi=result.roi, action="scale")
        if result.roi <= Decimal("0"):
            self._api.pause_campaign(result.campaign_id)
            return ProfitDecision(campaign_id=result.campaign_id, roi=result.roi, action="pause")
        return ProfitDecision(campaign_id=result.campaign_id, roi=result.roi, action="hold")
