from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np

from model import Policy

OUTPUT_PATH = Path("/shared-models/policy.pt")


def train_episode(data: Iterable[tuple[np.ndarray, float]]) -> str:
    model = Policy()
    for features, reward in data:
        model.train_step(features, reward)
    model.save(OUTPUT_PATH)
    return str(OUTPUT_PATH)
