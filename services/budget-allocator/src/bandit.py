from __future__ import annotations

import math


class UCBBandit:
    def __init__(self, n_arms: int) -> None:
        self.counts = [0.0 for _ in range(n_arms)]
        self.values = [0.0 for _ in range(n_arms)]

    def select(self) -> int:
        total = sum(self.counts) + 1.0
        scores = []
        for count, value in zip(self.counts, self.values):
            bonus = math.sqrt(2.0 * math.log(total) / (count + 1e-6))
            scores.append(value + bonus)
        return max(range(len(scores)), key=scores.__getitem__)

    def update(self, arm: int, reward: float) -> None:
        self.counts[arm] += 1.0
        count = self.counts[arm]
        value = self.values[arm]
        self.values[arm] = ((count - 1.0) / count) * value + (reward / count)
