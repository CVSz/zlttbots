from __future__ import annotations


def risk(severity: float, exploitability: float, reachability: float) -> float:
    """Compute a 0-10 risk score using weighted factors."""
    for value in (severity, exploitability, reachability):
        if value < 0 or value > 1:
            raise ValueError("risk inputs must be in [0, 1]")
    score = (severity * 0.5 + exploitability * 0.3 + reachability * 0.2) * 10
    return round(score, 2)
