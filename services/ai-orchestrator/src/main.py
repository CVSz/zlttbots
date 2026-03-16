from fastapi import FastAPI
import requests
import os
import redis

app = FastAPI()

REDIS = redis.Redis(host=os.getenv("REDIS_HOST","redis"),port=6379)

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/run-growth-cycle")
def run_growth_cycle():

    # 1 discover products
    r = requests.get("http://market-crawler:8000/crawl")

    # 2 predict viral score
    v = requests.post("http://viral-predictor:8000/predict")

    # 3 generate video
    g = requests.post("http://ai-video-generator:3000/render")

    # 4 publish
    p = requests.post("http://tiktok-uploader:3000/upload")

    REDIS.set("last_cycle","done")

    return {"status":"cycle-complete"}
