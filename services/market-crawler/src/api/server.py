from fastapi import FastAPI
from pydantic import BaseModel

from core.queue import enqueue

app = FastAPI()

class CrawlJob(BaseModel):
    keyword:str

@app.post("/crawl")

def crawl(job:CrawlJob):

    enqueue(job.dict())

    return {"status":"queued"}
