from __future__ import annotations


def long_term_reward(short_term: float, ltv: float, discount: float = 0.9) -> float:
    return float(short_term) + (float(discount) * float(ltv))
