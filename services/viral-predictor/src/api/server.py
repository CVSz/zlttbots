import os
import time

import psycopg2
from fastapi import FastAPI, Response
from pydantic import BaseModel
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from features.features import extract_features
from metrics import request_counter, request_latency
from model.model import predict

app = FastAPI()


class Video(BaseModel):
    views: int
    likes: int
    comments: int
    shares: int


@app.get('/healthz')
def healthz():
    db_url = os.environ.get('DB_URL')
    db_ok = False

    if db_url:
        try:
            with psycopg2.connect(db_url) as db:
                with db.cursor() as cur:
                    cur.execute('select 1')
                    cur.fetchone()
            db_ok = True
        except Exception:
            db_ok = False

    return {
        'status': 'ok',
        'service': 'viral-predictor',
        'checks': {
            'db': db_ok,
        },
    }


@app.get('/metrics')
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post('/predict')
def predict_viral(video: Video):
    start = time.perf_counter()
    video_payload = video.model_dump() if hasattr(video, 'model_dump') else video.dict()
    features = extract_features(video_payload)
    score = predict(features)
    request_counter.inc()
    request_latency.observe(time.perf_counter() - start)

    return {
        'viral_score': score,
    }
