from __future__ import annotations


class GlobalAllocator:
    def __init__(self, markets: list[str]) -> None:
        self.markets = markets
        self.weights = {market: 1.0 for market in markets}

    def allocate(self, total_budget: float) -> dict[str, float]:
        total_weight = sum(self.weights.values()) + 1e-8
        return {
            market: float((self.weights[market] / total_weight) * total_budget)
            for market in self.markets
        }

    def update(self, market: str, reward: float) -> None:
        if market not in self.weights:
            raise KeyError(f"unknown market: {market}")
        self.weights[market] *= max(0.0, 1.0 + reward)
