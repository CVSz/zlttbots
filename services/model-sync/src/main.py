from __future__ import annotations

import os
import shutil
from pathlib import Path

import requests

REGISTRY = os.getenv("MODEL_REGISTRY", "http://model-registry:8000")
LOCAL = Path(os.getenv("MODEL_SYNC_LOCAL_PATH", "/models"))
SHARED = Path(os.getenv("MODEL_SYNC_SHARED_PATH", "/shared-models"))
TIMEOUT = float(os.getenv("MODEL_SYNC_TIMEOUT", "5"))



def sync(name: str = "policy") -> str | None:
    LOCAL.mkdir(parents=True, exist_ok=True)
    response = requests.get(f"{REGISTRY}/latest/{name}", timeout=TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    model = payload.get("model")
    if not model:
        return None

    source = SHARED / model
    destination = LOCAL / model
    if not source.exists():
        raise FileNotFoundError(f"shared model not found: {source}")

    shutil.copy2(source, destination)
    current = LOCAL / f"{name}.pt"
    shutil.copy2(destination, current)
    return str(current)


if __name__ == "__main__":
    sync(os.getenv("MODEL_NAME", "policy"))
