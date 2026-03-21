from __future__ import annotations

import numpy as np


class Treasury:
    def __init__(self, capital: float = 10_000.0, hedge_limit: float = 0.5) -> None:
        self.capital = capital
        self.hedge_limit = hedge_limit

    def hedge(self, volatility: float) -> float:
        hedge_ratio = min(max(volatility, 0.0), self.hedge_limit)
        return float(self.capital * hedge_ratio)

    def allocate(self, expected_returns: list[float], risk_penalties: list[float] | None = None) -> np.ndarray:
        if not expected_returns:
            return np.asarray([], dtype=float)
        returns = np.asarray(expected_returns, dtype=float)
        penalties = np.asarray(risk_penalties if risk_penalties is not None else np.zeros_like(returns), dtype=float)
        adjusted = np.clip(returns - penalties, a_min=0.0, a_max=None)
        if float(adjusted.sum()) == 0.0:
            adjusted = np.full_like(adjusted, 1.0 / len(adjusted), dtype=float)
        weights = adjusted / adjusted.sum()
        return weights * self.capital
