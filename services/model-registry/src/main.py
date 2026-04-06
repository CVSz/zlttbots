from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Model Registry")
BASE = Path(os.getenv("MODEL_REGISTRY_PATH", "/models"))
SHARED = Path(os.getenv("MODEL_REGISTRY_SHARED_PATH", "/shared-models"))


def _ensure_writable_directory(path: Path, env_override_name: str) -> Path:
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except PermissionError:
        fallback = Path("/tmp/zttato-model-registry") / path.name
        fallback.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault(env_override_name, str(fallback))
        return fallback


BASE = _ensure_writable_directory(BASE, "MODEL_REGISTRY_PATH")
SHARED = _ensure_writable_directory(SHARED, "MODEL_REGISTRY_SHARED_PATH")


class Register(BaseModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    path: str = Field(min_length=1)


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "model-registry",
        "base_path": str(BASE),
    }


@app.post("/register")
def register(model: Register) -> dict[str, str]:
    source = Path(model.path)
    if not source.exists() or not source.is_file():
        raise HTTPException(status_code=400, detail=f"model path not found: {source}")

    destination = BASE / f"{model.name}_{model.version}.pt"
    shutil.copy2(source, destination)
    shutil.copy2(source, SHARED / destination.name)
    return {"stored": str(destination), "shared": str(SHARED / destination.name)}


@app.get("/latest/{name}")
def latest(name: str) -> dict[str, str | None]:
    files = sorted((path.name for path in BASE.glob(f"{name}_*.pt")), reverse=True)
    return {"model": files[0] if files else None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
