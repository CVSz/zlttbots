import os
import time

import redis
from fastapi import FastAPI, Response
from pydantic import BaseModel
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from core.queue import enqueue
from metrics import request_counter, request_latency

app = FastAPI()


class Job(BaseModel):
    input: str
    output: str


@app.get('/healthz')
def healthz():
    redis_ok = False

    try:
        redis_client = redis.Redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
        redis_ok = bool(redis_client.ping())
    except Exception:
        redis_ok = False

    return {
        'status': 'ok' if redis_ok else 'degraded',
        'service': 'gpu-renderer',
        'checks': {
            'redis': redis_ok,
        },
    }


@app.get('/metrics')
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post('/render')
def render_video(job: Job):
    start = time.perf_counter()
    payload = job.model_dump() if hasattr(job, 'model_dump') else job.dict()
    enqueue(payload)
    request_counter.inc()
    request_latency.observe(time.perf_counter() - start)
    return {'status': 'queued'}
