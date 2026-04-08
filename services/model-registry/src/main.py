from __future__ import annotations

import os
import re
import shutil
import stat
import tempfile
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
        fallback = Path("/tmp/zlttbots-model-registry") / path.name
        fallback.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault(env_override_name, str(fallback))
        return fallback


BASE = _ensure_writable_directory(BASE, "MODEL_REGISTRY_PATH")
SHARED = _ensure_writable_directory(SHARED, "MODEL_REGISTRY_SHARED_PATH")
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def _allowed_source_roots() -> tuple[Path, ...]:
    raw_roots = os.getenv("MODEL_REGISTRY_ALLOWED_SOURCE_ROOTS", "/tmp")
    configured = [item.strip() for item in raw_roots.split(":") if item.strip()]
    resolved_configured = [Path(item).expanduser().resolve(strict=False) for item in configured]
    return tuple(dict.fromkeys([BASE.resolve(strict=False), SHARED.resolve(strict=False), *resolved_configured]))


def _safe_model_component(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not SAFE_NAME_RE.fullmatch(cleaned):
        raise HTTPException(status_code=422, detail=f"invalid {field_name}")
    return cleaned


def _resolve_source_file(model_path: str) -> Path:
    candidate_input = Path(model_path).expanduser()
    source_name = _safe_model_component(candidate_input.name, "path")
    allowed_roots = _allowed_source_roots()
    candidate_paths: list[Path] = []
    if candidate_input.is_absolute():
        candidate_paths.append(candidate_input.resolve(strict=False))
    for allowed_root in allowed_roots:
        candidate_paths.append((allowed_root / source_name).resolve(strict=False))

    for candidate in candidate_paths:
        if not candidate.exists() or not candidate.is_file():
            continue
        if not _is_within_roots(candidate, allowed_roots):
            continue
        if candidate.is_symlink():
            raise HTTPException(status_code=400, detail="symlink source files are not allowed")
        mode = candidate.stat().st_mode
        if not stat.S_ISREG(mode):
            raise HTTPException(status_code=400, detail="source must be a regular file")
        return candidate
    raise HTTPException(status_code=400, detail="model path not found in allowed source roots")


def _resolve_destination(base_dir: Path, file_name: str) -> Path:
    candidate = (base_dir / file_name).resolve(strict=False)
    base_resolved = base_dir.resolve(strict=False)
    if candidate.parent != base_resolved:
        raise HTTPException(status_code=400, detail="invalid destination path")
    return candidate


def _is_within_roots(path: Path, roots: tuple[Path, ...]) -> bool:
    """
    Return True if ``path`` is contained within any of the given root directories.

    The check is performed on a normalized absolute path to avoid directory-traversal
    issues. Only paths that stay within one of the allowed roots after resolution
    are considered valid.
    """
    # Normalize the path first; `absolute()` avoids surprising behavior if a relative
    # path is passed in, and `resolve(strict=False)` collapses any ".." segments.
    resolved_path = path.absolute().resolve(strict=False)
    for root in roots:
        resolved_root = root.absolute().resolve(strict=False)
        try:
            # `relative_to` will raise ValueError if `resolved_path` is not under `resolved_root`.
            resolved_path.relative_to(resolved_root)
            return True
        except ValueError:
            continue
    return False


def _atomic_copy(source: Path, destination: Path) -> None:
    if not _is_within_roots(source, _allowed_source_roots()):
        raise HTTPException(status_code=400, detail="invalid source path")
    if not _is_within_roots(destination.parent, (BASE, SHARED)):
        raise HTTPException(status_code=400, detail="invalid destination path")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise HTTPException(status_code=409, detail="model version already exists")
    with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".tmp-", delete=False) as tmp_file:
        temp_path = Path(tmp_file.name)
    try:
        shutil.copy2(source, temp_path)
        os.chmod(temp_path, 0o600)
        os.replace(temp_path, destination)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


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

    destination_name = f"{safe_name}_{safe_version}.pt"
    destination = _resolve_destination(BASE, destination_name)
    shared_destination = _resolve_destination(SHARED, destination_name)
    if destination.exists() or shared_destination.exists():
        raise HTTPException(status_code=409, detail="model version already exists")
    _atomic_copy(source, destination)
    _atomic_copy(source, shared_destination)
    return {"stored": str(destination), "shared": str(shared_destination)}


@app.get("/latest/{name}")
def latest(name: str) -> dict[str, str | None]:
    safe_name = _safe_model_component(name, "name")
    files = sorted((path.name for path in BASE.glob(f"{safe_name}_*.pt")), reverse=True)
    return {"model": files[0] if files else None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
