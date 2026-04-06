import os
from contextlib import closing

import psycopg2
from fastapi import FastAPI, HTTPException

app = FastAPI()


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"CRITICAL: {name} is required but was not provided.")
    return value


def db():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=_required_env("POSTGRES_USER"),
        password=_required_env("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB", "zttato"),
    )


@app.post("/optimize")
def optimize():
    try:
        with closing(db()) as conn, closing(conn.cursor()) as cur:
            cur.execute("SELECT campaign_id, SUM(clicks) as c FROM clicks GROUP BY campaign_id")
            rows = cur.fetchall()

        best = max(rows, key=lambda x: x[1]) if rows else None

        return {"best_campaign": best}
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except psycopg2.Error as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
