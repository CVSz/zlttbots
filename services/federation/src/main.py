import base64
import hashlib
import hmac
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Federation Control Plane")
logger = logging.getLogger("federation")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
SECRET = os.getenv("FEDERATION_SECRET", "change-me")
DB_URL = os.getenv("DATABASE_URL", "postgresql://zlttbots:zlttbots@postgres:5432/zlttbots")
AUDIT_LOG_PATH = Path(os.getenv("FEDERATION_AUDIT_LOG", "/tmp/federation-audit.log"))
DEFAULT_TENANT = os.getenv("FEDERATION_DEFAULT_TENANT", "default")
def _safe_int_env(env_key: str, default_value: int) -> int:
    raw_value = os.getenv(env_key)
    if raw_value is None:
        return default_value
    try:
        parsed = int(raw_value)
    except ValueError:
        logger.warning(
            json.dumps(
                {
                    "event": "federation.invalid_env_int",
                    "env_key": env_key,
                    "raw_value": raw_value,
                    "default_used": default_value,
                }
            )
        )
        return default_value
    return parsed


def _safe_float_env(env_key: str, default_value: float) -> float:
    raw_value = os.getenv(env_key)
    if raw_value is None:
        return default_value
    value = raw_value.strip()
    if not value:
        return default_value
    try:
        parsed = float(value)
    except ValueError:
        logger.warning(
            json.dumps(
                {
                    "event": "federation.invalid_env_float",
                    "env_key": env_key,
                    "raw_value": raw_value,
                    "default_used": default_value,
                }
            )
        )
        return default_value
    return parsed


TOKEN_TTL_SECONDS = max(60, _safe_int_env("FEDERATION_TOKEN_TTL", 3600))
STARTUP_DB_MAX_ATTEMPTS = max(1, _safe_int_env("FEDERATION_DB_STARTUP_MAX_ATTEMPTS", 15))
STARTUP_DB_RETRY_SECONDS = max(1.0, _safe_float_env("FEDERATION_DB_STARTUP_RETRY_SECONDS", 2.0))


class NodeRegister(BaseModel):
    node_id: str = Field(min_length=6)
    region: str = Field(min_length=2)
    capacity: int = Field(ge=1)
    tenant_id: str = Field(default=DEFAULT_TENANT, min_length=1)
    labels: dict[str, str] = Field(default_factory=dict)
    attestation: str = Field(min_length=16)
    consent_approved: bool = Field(default=False)


class NodeRecord(NodeRegister):
    registered_at: int
    expires_at: int


def encode_signed_claims(claims: dict[str, Any]) -> str:
    payload = json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = hmac.new(SECRET.encode("utf-8"), payload, hashlib.sha256).digest()
    return f"{base64.urlsafe_b64encode(payload).decode('utf-8')}.{base64.urlsafe_b64encode(signature).decode('utf-8')}"


def db_connection():
    return psycopg2.connect(DB_URL)


def ensure_schema() -> None:
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS federation_nodes (
                    node_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    region TEXT NOT NULL,
                    capacity INTEGER NOT NULL,
                    labels JSONB NOT NULL DEFAULT '{}'::jsonb,
                    attestation TEXT NOT NULL,
                    consent_approved BOOLEAN NOT NULL DEFAULT FALSE,
                    registered_at BIGINT NOT NULL,
                    expires_at BIGINT NOT NULL
                )
                """
            )
        conn.commit()


@app.on_event("startup")
def startup() -> None:
    last_error: psycopg2.Error | None = None
    for attempt in range(1, STARTUP_DB_MAX_ATTEMPTS + 1):
        try:
            ensure_schema()
            logger.info(
                json.dumps(
                    {
                        "event": "federation.startup.db_ready",
                        "attempt": attempt,
                        "max_attempts": STARTUP_DB_MAX_ATTEMPTS,
                    }
                )
            )
            return
        except psycopg2.Error as exc:
            last_error = exc
            logger.warning(
                json.dumps(
                    {
                        "event": "federation.startup.db_retry",
                        "attempt": attempt,
                        "max_attempts": STARTUP_DB_MAX_ATTEMPTS,
                        "retry_seconds": STARTUP_DB_RETRY_SECONDS,
                        "error": str(exc),
                    }
                )
            )
            if attempt < STARTUP_DB_MAX_ATTEMPTS:
                time.sleep(STARTUP_DB_RETRY_SECONDS)
    raise RuntimeError("database unavailable during startup") from last_error


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    try:
        ensure_schema()
        database_ok = True
    except psycopg2.Error:
        database_ok = False
    return {
        "status": "ok" if database_ok else "degraded",
        "service": "federation",
        "checks": {"database": database_ok},
        "prometheus_labels": {"service": "federation", "component": "control-plane"},
    }


@app.get("/nodes")
def list_nodes() -> dict[str, Any]:
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT node_id, tenant_id, region, capacity, labels, attestation, consent_approved, registered_at, expires_at FROM federation_nodes WHERE expires_at >= %s ORDER BY registered_at DESC",
                    (int(time.time()),),
                )
                rows = cur.fetchall()
    except psycopg2.Error as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc

    nodes = [
        {
            "node_id": row[0],
            "tenant_id": row[1],
            "region": row[2],
            "capacity": row[3],
            "labels": row[4] or {},
            "attestation": row[5],
            "consent_approved": row[6],
            "registered_at": row[7],
            "expires_at": row[8],
        }
        for row in rows
    ]
    return {"nodes": nodes, "count": len(nodes)}


@app.post("/register")
def register(node: NodeRegister) -> dict[str, Any]:
    if not node.consent_approved:
        raise HTTPException(status_code=400, detail="node consent approval required")

    issued_at = int(time.time())
    expires_at = issued_at + TOKEN_TTL_SECONDS
    attestation_digest = hashlib.sha256(node.attestation.encode("utf-8")).hexdigest()
    token = encode_signed_claims(
        {
            "node_id": node.node_id,
            "tenant_id": node.tenant_id,
            "region": node.region,
            "attestation_sha256": attestation_digest,
            "iat": issued_at,
            "exp": expires_at,
            "token_type": "federation-node",
        }
    )

    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO federation_nodes (node_id, tenant_id, region, capacity, labels, attestation, consent_approved, registered_at, expires_at)
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
                    ON CONFLICT (node_id) DO UPDATE
                    SET tenant_id = EXCLUDED.tenant_id,
                        region = EXCLUDED.region,
                        capacity = EXCLUDED.capacity,
                        labels = EXCLUDED.labels,
                        attestation = EXCLUDED.attestation,
                        consent_approved = EXCLUDED.consent_approved,
                        registered_at = EXCLUDED.registered_at,
                        expires_at = EXCLUDED.expires_at
                    """,
                    (
                        node.node_id,
                        node.tenant_id,
                        node.region,
                        node.capacity,
                        json.dumps(node.labels),
                        attestation_digest,
                        node.consent_approved,
                        issued_at,
                        expires_at,
                    ),
                )
            conn.commit()
    except psycopg2.Error as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc

    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "event": "node.registered",
                    "node_id": node.node_id,
                    "tenant_id": node.tenant_id,
                    "region": node.region,
                    "capacity": node.capacity,
                    "labels": node.labels,
                    "attestation_sha256": attestation_digest,
                    "consent_approved": node.consent_approved,
                    "timestamp": issued_at,
                    "expires_at": expires_at,
                }
            )
            + "\n"
        )

    return {
        "token": token,
        "node": NodeRecord(**node.model_dump(), attestation=attestation_digest, registered_at=issued_at, expires_at=expires_at).model_dump(),
        "prometheus_labels": {"tenant_id": node.tenant_id, "region": node.region},
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
