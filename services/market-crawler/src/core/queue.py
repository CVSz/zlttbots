import redis
import os
import json

r = redis.Redis.from_url(
    os.environ.get("REDIS_URL","redis://localhost:6379")
)

def enqueue(job):
    r.lpush("crawl_jobs", json.dumps(job))

def dequeue():
    job = r.rpop("crawl_jobs")
    if not job:
        return None
    return json.loads(job)
