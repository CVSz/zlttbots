from fastapi import FastAPI
from pydantic import BaseModel
from core.queue import enqueue

app = FastAPI()

class Job(BaseModel):
    input:str
    output:str

@app.post("/render")

def render_video(job:Job):

    enqueue(job.dict())

    return {"status":"queued"}
