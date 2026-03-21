from __future__ import annotations

import random
from typing import Iterable


class HierarchicalRL:
    def __init__(self, dim: int = 2, lr: float = 0.01) -> None:
        self.lr = lr
        self.campaign_w = [random.uniform(-1.0, 1.0) for _ in range(dim)]
        self.adset_w = [random.uniform(-1.0, 1.0) for _ in range(dim)]
        self.creative_w = [random.uniform(-1.0, 1.0) for _ in range(dim)]

    @staticmethod
    def _dot(lhs: list[float], rhs: list[float]) -> float:
        return float(sum(a * b for a, b in zip(lhs, rhs)))

    @staticmethod
    def _vector(values: Iterable[float]) -> list[float]:
        return [float(value) for value in values]

    def select(self, x: Iterable[float]) -> dict[str, int]:
        vector = self._vector(x)
        return {
            "campaign": int(self._dot(self.campaign_w, vector) > 0.0),
            "adset": int(self._dot(self.adset_w, vector) > 0.0),
            "creative": int(self._dot(self.creative_w, vector) > 0.0),
        }

    def update(self, x: Iterable[float], reward: float, lr: float | None = None) -> None:
        vector = self._vector(x)
        step = self.lr if lr is None else float(lr)
        delta = [step * float(reward) * value for value in vector]
        self.campaign_w = [weight + change for weight, change in zip(self.campaign_w, delta)]
        self.adset_w = [weight + change for weight, change in zip(self.adset_w, delta)]
        self.creative_w = [weight + change for weight, change in zip(self.creative_w, delta)]
