from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Nation:
    gdp: float = field(default_factory=lambda: float(np.random.rand() * 1e6))
    tech: float = field(default_factory=lambda: float(np.random.rand()))
    military: float = field(default_factory=lambda: float(np.random.rand()))

    def policy(self) -> None:
        invest = self.gdp * 0.05
        self.tech += invest * 1e-6
        self.military += invest * 1e-7
        self.gdp *= 1 + self.tech * 0.01 - self.military * 0.005


class World:
    def __init__(self, n: int = 5) -> None:
        self.nations = [Nation() for _ in range(n)]

    def step(self) -> None:
        for nation in self.nations:
            nation.policy()

    def metrics(self) -> dict[str, float]:
        return {
            "global_gdp": float(sum(nation.gdp for nation in self.nations)),
            "avg_tech": float(np.mean([nation.tech for nation in self.nations])),
        }
