from __future__ import annotations

import json
from pathlib import Path

import numpy as np

MODEL_PATH = Path(__file__).resolve().parents[1] / "viral_model.json"
FEATURE_COUNT = 5
DEFAULT_WEIGHTS = np.array([1e-6, 2e-4, 4e-4, 6e-4, 3.5], dtype=float)
DEFAULT_BIAS = -2.0


class ViralNet:
    def __init__(self, weights: np.ndarray | None = None, bias: float = DEFAULT_BIAS):
        self.weights = np.array(weights if weights is not None else DEFAULT_WEIGHTS, dtype=float)
        self.bias = float(bias)

    def forward(self, x: np.ndarray) -> np.ndarray:
        logits = x @ self.weights + self.bias
        return 1.0 / (1.0 + np.exp(-np.clip(logits, -50.0, 50.0)))

    def save(self, path: Path = MODEL_PATH) -> None:
        path.write_text(json.dumps({"weights": self.weights.tolist(), "bias": self.bias}), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = MODEL_PATH) -> "ViralNet":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(weights=np.array(data["weights"], dtype=float), bias=float(data["bias"]))


model = ViralNet.load()


def predict(features: np.ndarray) -> float:
    feature_array = np.asarray(features, dtype=float).reshape(1, FEATURE_COUNT)
    score = model.forward(feature_array)[0]
    return float(score)
