from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


class ROIRepository(Protocol):
    def fetch_revenue(self, campaign_id: str) -> Decimal: ...

    def fetch_cost(self, campaign_id: str) -> Decimal: ...


@dataclass(frozen=True)
class ROIResult:
    campaign_id: str
    revenue: Decimal
    cost: Decimal
    roi: Decimal

    @property
    def profitable(self) -> bool:
        return self.roi >= Decimal("1")


class ROIEngine:
    """Deterministic ROI calculator used by orchestration loops."""

    def __init__(self, repo: ROIRepository):
        self._repo = repo

    def evaluate(self, campaign_id: str) -> ROIResult:
        cid = campaign_id.strip()
        if not cid:
            raise ValueError("campaign_id is required")

        revenue = self._repo.fetch_revenue(cid)
        cost = self._repo.fetch_cost(cid)
        roi = Decimal("0") if cost <= Decimal("0") else (revenue / cost)
        return ROIResult(campaign_id=cid, revenue=revenue, cost=cost, roi=roi)
