import os

import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel

from features.features import extract_features
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


@app.post('/predict')
def predict_viral(video: Video):
    features = extract_features(video.dict())
    score = predict(features)

    return {
        'viral_score': score,
    }
