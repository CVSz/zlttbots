from __future__ import annotations

import os
import re
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
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def _safe_model_component(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not SAFE_NAME_RE.fullmatch(cleaned):
        raise HTTPException(status_code=422, detail=f"invalid {field_name}")
    return cleaned


def _resolve_source_file(model_path: str) -> Path:
    candidate = Path(model_path).expanduser().resolve(strict=False)
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=400, detail="model path not found")

    base_allowed = BASE.resolve(strict=False)
    shared_allowed = SHARED.resolve(strict=False)
    if not (candidate.is_relative_to(base_allowed) or candidate.is_relative_to(shared_allowed)):
        raise HTTPException(status_code=400, detail="model path is outside allowed registries")
    return candidate


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
    source = _resolve_source_file(model.path)
    safe_name = _safe_model_component(model.name, "name")
    safe_version = _safe_model_component(model.version, "version")

    destination = BASE / f"{safe_name}_{safe_version}.pt"
    shutil.copy2(source, destination)
    shutil.copy2(source, SHARED / destination.name)
    return {"stored": str(destination), "shared": str(SHARED / destination.name)}


@app.get("/latest/{name}")
def latest(name: str) -> dict[str, str | None]:
    safe_name = _safe_model_component(name, "name")
    files = sorted((path.name for path in BASE.glob(f"{safe_name}_*.pt")), reverse=True)
    return {"model": files[0] if files else None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
