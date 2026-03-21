from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression


class TLearner:
    def __init__(self) -> None:
        self.model_t = LogisticRegression(max_iter=1000)
        self.model_c = LogisticRegression(max_iter=1000)

    def fit(self, X: np.ndarray, treatment: np.ndarray, y: np.ndarray) -> None:
        treatment_mask = treatment == 1
        control_mask = treatment == 0
        if not np.any(treatment_mask) or not np.any(control_mask):
            raise ValueError("TLearner requires both treated and control samples")
        self.model_t.fit(X[treatment_mask], y[treatment_mask])
        self.model_c.fit(X[control_mask], y[control_mask])

    def predict_uplift(self, X: np.ndarray) -> np.ndarray:
        pt = self.model_t.predict_proba(X)[:, 1]
        pc = self.model_c.predict_proba(X)[:, 1]
        return pt - pc
