import os
import json
import redis

r = redis.Redis.from_url(os.environ.get("REDIS_URL","redis://localhost:6379"))

def enqueue(job):
    r.lpush("render_jobs", json.dumps(job))

def dequeue():
    job = r.rpop("render_jobs")
    if not job:
        return None
    return json.loads(job)
