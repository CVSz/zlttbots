from __future__ import annotations


def compute_reward(revenue: float, cost: float, risk: float = 0.0) -> float:
    """Profit-aware reward that discounts risk-sensitive actions."""
    profit = revenue - cost
    penalty = max(risk, 0.0) * 0.1
    return float(profit - penalty)
