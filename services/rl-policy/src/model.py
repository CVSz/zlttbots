from __future__ import annotations

import json
from pathlib import Path

import numpy as np


class Policy:
    def __init__(self) -> None:
        self.w1 = np.array([[0.15, -0.05], [0.08, 0.12]], dtype=float)
        self.b1 = np.array([0.01, -0.02], dtype=float)
        self.w2 = np.array([[0.2, -0.1], [-0.15, 0.18]], dtype=float)
        self.b2 = np.array([0.0, 0.0], dtype=float)

    def forward(self, x: np.ndarray) -> np.ndarray:
        hidden = np.maximum((x @ self.w1) + self.b1, 0.0)
        logits = (hidden @ self.w2) + self.b2
        logits = logits - logits.max(axis=1, keepdims=True)
        exp = np.exp(logits)
        return exp / exp.sum(axis=1, keepdims=True)

    __call__ = forward

    def train_step(self, x: np.ndarray, reward: float, learning_rate: float = 1e-2) -> None:
        probs = self.forward(x)[0]
        advantage = float(max(-1.0, min(1.0, reward)))
        gradient = np.array([-probs[0], 1.0 - probs[1]], dtype=float) * advantage
        self.b2 += learning_rate * gradient

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({
            "w1": self.w1.tolist(),
            "b1": self.b1.tolist(),
            "w2": self.w2.tolist(),
            "b2": self.b2.tolist(),
        }))

    @classmethod
    def load(cls, path: str | Path) -> "Policy":
        instance = cls()
        payload = json.loads(Path(path).read_text())
        instance.w1 = np.array(payload["w1"], dtype=float)
        instance.b1 = np.array(payload["b1"], dtype=float)
        instance.w2 = np.array(payload["w2"], dtype=float)
        instance.b2 = np.array(payload["b2"], dtype=float)
        return instance
