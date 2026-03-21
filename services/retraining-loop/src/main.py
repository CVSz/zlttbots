from __future__ import annotations

import os
import time
from typing import Any

import requests

RL_POLICY_URL = os.getenv("RL_POLICY_URL", "http://rl-policy:8000")
MODEL_REGISTRY_URL = os.getenv("MODEL_REGISTRY_URL", "http://model-registry:8000")
MODEL_ARTIFACT_PATH = os.getenv("MODEL_ARTIFACT_PATH", "/tmp/policy.pt")
SLEEP_SECONDS = int(os.getenv("RETRAINING_INTERVAL_SECONDS", "300"))
TIMEOUT = float(os.getenv("RETRAINING_TIMEOUT", "10"))



def trigger_once() -> dict[str, Any] | None:
    response = requests.post(f"{RL_POLICY_URL}/train", timeout=TIMEOUT)
    response.raise_for_status()

    version = str(int(time.time()))
    registry = requests.post(
        f"{MODEL_REGISTRY_URL}/register",
        json={"name": "policy", "version": version, "path": MODEL_ARTIFACT_PATH},
        timeout=TIMEOUT,
    )
    registry.raise_for_status()
    return {"version": version, "registry": registry.json(), "training": response.json()}


if __name__ == "__main__":
    while True:
        trigger_once()
        time.sleep(SLEEP_SECONDS)
