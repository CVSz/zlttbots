from __future__ import annotations

import shutil
from pathlib import Path

MODEL_DIR = Path("/models")
BACKUP_DIR = Path("/models_backup")
MODEL_NAME = "policy.onnx"


def backup() -> Path:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    source = MODEL_DIR / MODEL_NAME
    destination = BACKUP_DIR / MODEL_NAME
    if source.exists():
        shutil.copyfile(source, destination)
    return destination


def rollback() -> Path:
    source = BACKUP_DIR / MODEL_NAME
    destination = MODEL_DIR / MODEL_NAME
    if not source.exists():
        raise FileNotFoundError(f"backup model not found: {source}")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return destination
