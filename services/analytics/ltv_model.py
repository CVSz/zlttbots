from __future__ import annotations

from typing import Iterable


class LTVModel:
    def predict(self, features: Iterable[float]) -> float:
        vector = [float(value) for value in features]
        coeffs = [1.2, 0.8]
        return float(sum(value * coeff for value, coeff in zip(vector, coeffs)))
