import hashlib
import os
import secrets
from typing import Any

import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Tenant Service")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://zttato:zttato@postgres:5432/zttato")
DEFAULT_DAILY_SPEND_LIMIT = float(os.getenv("DEFAULT_DAILY_SPEND_LIMIT", "100.0"))


def db_connection():
    return psycopg2.connect(DATABASE_URL)


class TenantCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    plan: str = Field(default="free", min_length=2, max_length=50)
    region: str = Field(default="US", min_length=2, max_length=8)
    daily_spend_limit: float = Field(default=DEFAULT_DAILY_SPEND_LIMIT, gt=0)


class TenantCreateResponse(BaseModel):
    tenant_id: int
    api_key: str
    plan: str
    region: str
    daily_spend_limit: float


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        database_ok = True
    except psycopg2.Error:
        database_ok = False

    return {"status": "ok" if database_ok else "degraded", "service": "tenant-service", "checks": {"database": database_ok}}


@app.post("/tenant", response_model=TenantCreateResponse)
def create_tenant(payload: TenantCreateRequest) -> TenantCreateResponse:
    api_key = f"zt_{secrets.token_urlsafe(24)}"
    api_key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tenants (name, plan, region, api_key_hash, daily_spend_limit)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, plan, region, daily_spend_limit
                    """,
                    (payload.name, payload.plan, payload.region.upper(), api_key_hash, payload.daily_spend_limit),
                )
                tenant_id, plan, region, daily_spend_limit = cur.fetchone()
    except psycopg2.errors.UniqueViolation as exc:
        raise HTTPException(status_code=409, detail="tenant already exists") from exc
    except psycopg2.Error as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc

    return TenantCreateResponse(
        tenant_id=tenant_id,
        api_key=api_key,
        plan=plan,
        region=region,
        daily_spend_limit=float(daily_spend_limit),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
