from __future__ import annotations

import time

import numpy as np

from psi import psi

baseline = np.random.rand(1000)


def loop() -> None:
    while True:
        current = np.random.rand(1000)
        score = psi(baseline, current)
        if score > 0.2:
            print(f"⚠️ DRIFT DETECTED: {score:.4f}")
        time.sleep(10)


if __name__ == "__main__":
    loop()
