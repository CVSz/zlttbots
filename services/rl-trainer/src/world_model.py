from __future__ import annotations

import numpy as np


class WorldModel:
    def __init__(self, dim: int = 2, lr: float = 0.01) -> None:
        self.lr = lr
        self.W = np.random.randn(dim, dim)

    def predict_next(self, state: np.ndarray) -> np.ndarray:
        vector = np.asarray(state, dtype=float)
        return np.tanh(vector @ self.W)

    def update(self, state: np.ndarray, next_state: np.ndarray) -> np.ndarray:
        vector = np.asarray(state, dtype=float)
        target = np.asarray(next_state, dtype=float)
        pred = self.predict_next(vector)
        grad = target - pred
        self.W += self.lr * np.outer(vector, grad)
        return pred
