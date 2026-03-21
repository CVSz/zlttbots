from __future__ import annotations

import numpy as np


def psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    expected_perc, _ = np.histogram(expected, bins=bins)
    actual_perc, _ = np.histogram(actual, bins=bins)
    expected_share = expected_perc / max(len(expected), 1)
    actual_share = actual_perc / max(len(actual), 1)
    return float(np.sum((actual_share - expected_share) * np.log((actual_share + 1e-6) / (expected_share + 1e-6))))
