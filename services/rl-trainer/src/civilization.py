from __future__ import annotations

import numpy as np


class CivAgent:
    def __init__(self) -> None:
        self.tech = float(np.random.rand())
        self.capital = float(np.random.rand() * 100.0)

    def act(self) -> None:
        invest = float(np.random.rand() * self.capital * 0.1)
        self.tech += invest * 0.01
        self.capital += (self.tech - 0.5) * 2.0


class Civilization:
    def __init__(self, n: int = 20) -> None:
        self.agents = [CivAgent() for _ in range(n)]

    def step(self) -> None:
        for agent in self.agents:
            agent.act()

    def metrics(self) -> dict[str, float]:
        return {
            "avg_capital": float(np.mean([agent.capital for agent in self.agents])),
            "avg_tech": float(np.mean([agent.tech for agent in self.agents])),
        }
