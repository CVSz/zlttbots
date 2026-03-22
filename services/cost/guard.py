from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class DailyCostGuard:
    max_daily_cost: float
    spent: float = 0.0

    def allow(self, cost: float) -> bool:
        if cost < 0:
            raise ValueError("cost must be non-negative")
        if self.spent + cost > self.max_daily_cost:
            return False
        self.spent += cost
        return True

    def reset(self) -> None:
        self.spent = 0.0


def from_env() -> DailyCostGuard:
    return DailyCostGuard(max_daily_cost=float(os.getenv("MAX_DAILY_COST", "300")))
