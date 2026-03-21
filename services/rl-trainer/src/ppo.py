from __future__ import annotations

import numpy as np


class PPO:
    def __init__(self, dim: int = 2, lr: float = 0.001, clip: float = 0.2) -> None:
        self.w = np.random.randn(dim)
        self.lr = lr
        self.clip = clip

    def policy(self, x: np.ndarray) -> float:
        z = float(np.dot(self.w, x))
        return float(1.0 / (1.0 + np.exp(-z)))

    def update(self, x: np.ndarray, reward: float, old_prob: float) -> float:
        prob = self.policy(x)
        ratio = prob / (old_prob + 1e-8)
        clipped_ratio = float(np.clip(ratio, 1 - self.clip, 1 + self.clip))
        advantage = min(ratio * reward, clipped_ratio * reward)
        grad = advantage * x
        self.w += self.lr * grad
        return prob
