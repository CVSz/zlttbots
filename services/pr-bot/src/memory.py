from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ReviewMemory:
    repo: str
    file: str
    embedding: list[float]
    issue: str
    fix: str
    severity: str
    timestamp: datetime


class ReviewMemoryStore:
    def __init__(self, db_url: str, embedding_dimensions: int = 1536) -> None:
        self._db_url = db_url
        self._embedding_dimensions = embedding_dimensions

    def _validate_embedding(self, embedding: list[float]) -> None:
        if len(embedding) != self._embedding_dimensions:
            raise ValueError(
                f"embedding must have {self._embedding_dimensions} dimensions, got {len(embedding)}"
            )

    def insert_memory(self, item: ReviewMemory) -> None:
        self._validate_embedding(item.embedding)
        import psycopg

        with psycopg.connect(self._db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO review_memory (repo, file, embedding, issue, fix, severity, created_at)
                    VALUES (%s, %s, %s::vector, %s, %s, %s, %s)
                    """,
                    (
                        item.repo,
                        item.file,
                        json.dumps(item.embedding),
                        item.issue,
                        item.fix,
                        item.severity,
                        item.timestamp.astimezone(timezone.utc),
                    ),
                )
            conn.commit()

    def search_similar(self, embedding: list[float], limit: int = 5) -> list[dict[str, Any]]:
        self._validate_embedding(embedding)
        import psycopg

        with psycopg.connect(self._db_url) as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    """
                    SELECT id, repo, file, issue, fix, severity, created_at
                    FROM review_memory
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (json.dumps(embedding), limit),
                )
                return list(cur.fetchall())
