from __future__ import annotations

import numpy as np


class MetaLearner:
    def __init__(self, lr: float = 0.01, floor: float = 1e-4, ceiling: float = 0.1) -> None:
        self.lr = lr
        self.floor = floor
        self.ceiling = ceiling

    def adapt(self, reward_history: list[float]) -> float:
        window = reward_history[-10:] if reward_history else [0.0]
        trend = float(np.mean(window))
        self.lr *= 0.9 if trend < 0 else 1.05
        self.lr = float(np.clip(self.lr, self.floor, self.ceiling))
        return self.lr
