from __future__ import annotations


def doubly_robust(reward: float, propensity: float, model_pred: float) -> float:
    safe_propensity = max(float(propensity), 1e-6)
    baseline = float(model_pred)
    observed_reward = float(reward)
    return baseline + ((observed_reward - baseline) / safe_propensity)
