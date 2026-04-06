from __future__ import annotations

import math


class HybridRL:
    """Hybrid exploration strategy that combines UCB with a lightweight policy term."""

    @staticmethod
    def _initial_policy_weights(feature_dim: int) -> list[float]:
        return [((index + 1) / (feature_dim + 1)) * 2.0 - 1.0 for index in range(feature_dim)]

    def __init__(self, n_arms: int = 5, feature_dim: int = 2, lr: float = 0.01) -> None:
        self.counts = [0.0 for _ in range(n_arms)]
        self.values = [0.0 for _ in range(n_arms)]
        self.policy_w = self._initial_policy_weights(feature_dim)
        self.lr = float(lr)

    def select_arm(self, x: list[float]) -> int:
        total = sum(self.counts) + 1.0
        policy_score = sum(weight * feature for weight, feature in zip(self.policy_w, x))
        scores = []
        for value, count in zip(self.values, self.counts):
            bonus = math.sqrt(2.0 * math.log(total) / (count + 1e-6))
            scores.append(value + bonus + policy_score)
        return max(range(len(scores)), key=scores.__getitem__)

    def update(self, arm: int, reward: float, x: list[float]) -> None:
        self.counts[arm] += 1.0
        self.values[arm] += (reward - self.values[arm]) / self.counts[arm]
        self.policy_w = [weight + (self.lr * reward * feature) for weight, feature in zip(self.policy_w, x)]
