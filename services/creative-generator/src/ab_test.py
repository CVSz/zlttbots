from __future__ import annotations

import random


class CreativeAB:
    def __init__(self) -> None:
        self.stats: dict[str, list[float]] = {}

    def update(self, creative_id: str, reward: bool | float) -> None:
        if creative_id not in self.stats:
            self.stats[creative_id] = [1.0, 1.0]
        alpha, beta = self.stats[creative_id]
        reward_value = float(reward)
        self.stats[creative_id] = [alpha + reward_value, beta + (1.0 - reward_value)]

    def select(self) -> str:
        if not self.stats:
            raise ValueError("no creatives registered")
        samples = {
            creative_id: random.betavariate(alpha, beta)
            for creative_id, (alpha, beta) in self.stats.items()
        }
        return max(samples, key=samples.get)
