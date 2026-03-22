from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class UnitEconomics:
    campaign_id: str
    revenue: Decimal
    cost: Decimal
    acquisitions: int
    active_customers: int

    @property
    def profit(self) -> Decimal:
        return self.revenue - self.cost

    @property
    def cpa(self) -> Decimal:
        if self.acquisitions <= 0:
            return Decimal("0")
        return self.cost / Decimal(self.acquisitions)

    @property
    def ltv(self) -> Decimal:
        if self.active_customers <= 0:
            return Decimal("0")
        return self.revenue / Decimal(self.active_customers)

    @property
    def roas(self) -> Decimal:
        if self.cost <= Decimal("0"):
            return Decimal("0")
        return self.revenue / self.cost

    @property
    def profitable(self) -> bool:
        return self.profit >= Decimal("0")
