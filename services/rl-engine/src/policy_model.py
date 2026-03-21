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

    def load_state_dict(self, payload: dict[str, list[list[float]] | list[float]]) -> None:
        self.w1 = np.array(payload["w1"], dtype=float)
        self.b1 = np.array(payload["b1"], dtype=float)
        self.w2 = np.array(payload["w2"], dtype=float)
        self.b2 = np.array(payload["b2"], dtype=float)

    @classmethod
    def load(cls, path: str | Path) -> "Policy":
        payload = json.loads(Path(path).read_text())
        instance = cls()
        instance.load_state_dict(payload)
        return instance
