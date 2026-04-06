import logging
import os
import time
from typing import Any

import msgpack
from redis import Redis
from redis.cluster import RedisCluster

log = logging.getLogger("model-service.result-store")
RESULT_TTL_SECONDS = int(os.getenv("RESULT_TTL", "3600"))
RESULT_NAMESPACE = os.getenv("RESULT_NAMESPACE", "result")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
REDIS_CLUSTER_URL = os.getenv("REDIS_CLUSTER_URL", "")


def _sanitize_log_value(value: str) -> str:
    return value.replace("\r", " ").replace("\n", " ").strip()


class ResultStore:
    def __init__(self) -> None:
        self._client = self._build_client()

    def _build_client(self) -> Redis | RedisCluster:
        if REDIS_CLUSTER_URL:
            log.info("Connecting to Redis cluster at %s", REDIS_CLUSTER_URL)
            return RedisCluster.from_url(REDIS_CLUSTER_URL, decode_responses=False)
        return Redis.from_url(REDIS_URL, decode_responses=False)

    def _key(self, job_id: str) -> str:
        return f"{RESULT_NAMESPACE}:{job_id}"

    def set_result(self, job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not job_id:
            raise ValueError("job_id is required")

        data = {
            "job_id": job_id,
            "status": payload.get("status", "done"),
            "score": payload.get("score"),
            "ctr": payload.get("ctr"),
            "cvr": payload.get("cvr"),
            "model_version": payload.get("model_version"),
            "error": payload.get("error"),
            "updated_at": int(time.time()),
        }
        packed = msgpack.packb(data, use_bin_type=True)
        self._client.setex(self._key(job_id), RESULT_TTL_SECONDS, packed)
        return data

    def get_result(self, job_id: str) -> dict[str, Any] | None:
        if not job_id:
            return None

        raw = self._client.get(self._key(job_id))
        if not raw:
            return None

        try:
            decoded = msgpack.unpackb(raw, raw=False)
            if isinstance(decoded, dict):
                return decoded
        except Exception:  # pragma: no cover - defensive fallback
            log.warning("Failed to decode result for job_id=%s", _sanitize_log_value(job_id), exc_info=True)
        return None


result_store = ResultStore()
