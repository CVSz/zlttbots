import json
import logging
import os
import re
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}')
logger = logging.getLogger("security-api")


class Settings(BaseModel):
    scan_root: Path = Path(os.getenv("SCAN_ROOT", "/tmp/zttato-scans"))
    service_api_key: str = os.getenv("SECURITY_API_KEY", "")
    git_clone_timeout_seconds: int = Field(default=int(os.getenv("GIT_CLONE_TIMEOUT_SECONDS", "180")), ge=30, le=1800)
    codeql_timeout_seconds: int = Field(default=int(os.getenv("CODEQL_TIMEOUT_SECONDS", "600")), ge=60, le=3600)


class ScanRequest(BaseModel):
    repo_url: str = Field(min_length=1, max_length=2048)
    language: Literal["python", "javascript", "java", "go", "ruby", "cpp", "csharp"] = "python"


class ScanRecord(BaseModel):
    scan_id: str
    status: Literal["queued", "running", "completed", "failed"]
    repo_url: str
    created_at: datetime
    updated_at: datetime
    result_path: str | None = None
    error: str | None = None


class ScanStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: dict[str, ScanRecord] = {}

    def save(self, record: ScanRecord) -> None:
        with self._lock:
            self._records[record.scan_id] = record

    def get(self, scan_id: str) -> ScanRecord:
        with self._lock:
            if scan_id not in self._records:
                raise KeyError(scan_id)
            return self._records[scan_id]


def _validate_repo_url(repo_url: str) -> str:
    parsed = urlparse(repo_url)
    if parsed.scheme != "https":
        raise HTTPException(status_code=400, detail="Only HTTPS repositories are allowed")
    if parsed.hostname not in {"github.com", "gitlab.com", "bitbucket.org"}:
        raise HTTPException(status_code=400, detail="Repository host is not allowed")
    if not re.fullmatch(r"/[\w.-]+/[\w.-]+(?:\.git)?", parsed.path):
        raise HTTPException(status_code=400, detail="Repository path is invalid")
    if parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise HTTPException(status_code=400, detail="Repository URL must not include credentials, query, or fragment")
    return repo_url


def _require_api_key(x_api_key: str | None, settings: Settings) -> None:
    if not settings.service_api_key:
        raise HTTPException(status_code=500, detail="SECURITY_API_KEY is not configured")
    if x_api_key != settings.service_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _run_scan(scan_id: str, request: ScanRequest, settings: Settings, store: ScanStore) -> None:
    now = datetime.now(tz=timezone.utc)
    record = store.get(scan_id)
    record.status = "running"
    record.updated_at = now
    store.save(record)

    scan_dir = settings.scan_root / scan_id
    repo_dir = scan_dir / "repo"
    result_path = scan_dir / "result.sarif"
    db_path = scan_dir / "db"
    scan_dir.mkdir(parents=True, exist_ok=False)

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", request.repo_url, str(repo_dir)],
            check=True,
            timeout=settings.git_clone_timeout_seconds,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["codeql", "database", "create", str(db_path), "--source-root", str(repo_dir), "--language", request.language],
            check=True,
            timeout=settings.codeql_timeout_seconds,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["codeql", "database", "analyze", str(db_path), "--format", "sarif-latest", "--output", str(result_path)],
            check=True,
            timeout=settings.codeql_timeout_seconds,
            capture_output=True,
            text=True,
        )

        record.status = "completed"
        record.result_path = str(result_path)
        record.updated_at = datetime.now(tz=timezone.utc)
        store.save(record)
    except (subprocess.SubprocessError, OSError) as exc:
        logger.exception("scan failed", extra={"scan_id": scan_id})
        record.status = "failed"
        record.error = str(exc)
        record.updated_at = datetime.now(tz=timezone.utc)
        store.save(record)


app = FastAPI(title="Security API", version="1.0.0")
settings = Settings()
store = ScanStore()
settings.scan_root.mkdir(parents=True, exist_ok=True)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "security-api"}


@app.post("/scan")
def run_scan(payload: ScanRequest, background_tasks: BackgroundTasks, x_api_key: str | None = Header(default=None)) -> dict[str, str]:
    _require_api_key(x_api_key, settings)
    safe_repo_url = _validate_repo_url(payload.repo_url)

    scan_id = str(uuid.uuid4())
    now = datetime.now(tz=timezone.utc)
    record = ScanRecord(
        scan_id=scan_id,
        status="queued",
        repo_url=safe_repo_url,
        created_at=now,
        updated_at=now,
    )
    store.save(record)

    sanitized_payload = ScanRequest(repo_url=safe_repo_url, language=payload.language)
    background_tasks.add_task(_run_scan, scan_id, sanitized_payload, settings, store)

    return {"scan_id": scan_id, "status": "started"}


@app.get("/scan/{scan_id}")
def get_scan(scan_id: str, x_api_key: str | None = Header(default=None)) -> dict[str, object]:
    _require_api_key(x_api_key, settings)
    try:
        record = store.get(scan_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="scan not found") from exc

    payload = record.model_dump(mode="json")
    if record.result_path and Path(record.result_path).exists():
        with open(record.result_path, "r", encoding="utf-8") as sarif_file:
            payload["result"] = json.load(sarif_file)
    return payload
