import os

import redis
from fastapi import FastAPI
from pydantic import BaseModel

from core.queue import enqueue

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


@app.post('/render')
def render_video(job: Job):
    payload = job.model_dump() if hasattr(job, "model_dump") else job.dict()
    enqueue(payload)
    return {'status': 'queued'}
