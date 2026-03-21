from __future__ import annotations

import numpy as np
import pandas as pd

from model.model import FEATURE_COUNT, ViralNet

FEATURE_COLUMNS = ["views", "likes", "comments", "shares", "engagement"]
TARGET_COLUMN = "viral"


def _sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(values, -50.0, 50.0)))


def train(datafile: str, epochs: int = 1500, learning_rate: float = 0.1) -> ViralNet:
    df = pd.read_csv(datafile)
    X = df[FEATURE_COLUMNS].to_numpy(dtype=float)
    y = df[TARGET_COLUMN].to_numpy(dtype=float)

    if X.shape[1] != FEATURE_COUNT:
        raise ValueError(f"Expected {FEATURE_COUNT} features, got {X.shape[1]}")

    means = X.mean(axis=0)
    stds = np.where(X.std(axis=0) == 0.0, 1.0, X.std(axis=0))
    X_scaled = (X - means) / stds

    weights = np.zeros(FEATURE_COUNT, dtype=float)
    bias = 0.0

    sample_count = len(X_scaled)
    for _ in range(epochs):
        logits = X_scaled @ weights + bias
        predictions = _sigmoid(logits)
        errors = predictions - y

        weights -= learning_rate * (X_scaled.T @ errors) / sample_count
        bias -= learning_rate * errors.mean()

    scaled_weights = weights / stds
    scaled_bias = bias - np.dot(means / stds, weights)

    model = ViralNet(weights=scaled_weights, bias=scaled_bias)
    model.save()
    return model
