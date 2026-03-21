from __future__ import annotations

from typing import Iterable


class CapitalEngine:
    def __init__(self, capital: float = 1000.0) -> None:
        self.capital = float(capital)

    def reinvest(self, returns: Iterable[float]) -> float:
        values = [float(value) for value in returns]
        growth = (sum(values) / len(values)) if values else 0.0
        self.capital *= 1.0 + growth
        return self.capital

    def allocate(self, opportunities: Iterable[float]) -> list[float]:
        weights = [float(value) for value in opportunities]
        total = sum(weights) + 1e-8
        return [(weight / total) * self.capital for weight in weights]
