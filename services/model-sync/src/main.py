from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from sync import download, upload

REGISTRY = os.getenv("MODEL_REGISTRY", "http://model-registry:8000")
LOCAL = Path(os.getenv("MODEL_SYNC_LOCAL_PATH", "/models"))
SHARED = Path(os.getenv("MODEL_SYNC_SHARED_PATH", "/shared-models"))
TIMEOUT = float(os.getenv("MODEL_SYNC_TIMEOUT", "5"))


def sync(name: str = "policy") -> str | None:
    LOCAL.mkdir(parents=True, exist_ok=True)
    source = SHARED / f"{name}.onnx"
    if source.exists():
        destination = LOCAL / source.name
        destination.write_bytes(source.read_bytes())
        current = LOCAL / f"{name}.onnx"
        current.write_bytes(destination.read_bytes())
        return str(current)
    try:
        download()
    except Exception:
        return None
    return str(LOCAL / f"{name}.onnx")


if __name__ == "__main__":
    model = sync(os.getenv("MODEL_NAME", "policy"))
    print(json.dumps({"model": model, "registry": REGISTRY, "timeout": TIMEOUT}))
