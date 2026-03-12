from fastapi import FastAPI
from pydantic import BaseModel

from features.features import extract_features
from model.model import predict

app = FastAPI()


class Video(BaseModel):

    views:int
    likes:int
    comments:int
    shares:int


@app.post("/predict")

def predict_viral(video:Video):

    features = extract_features(video.dict())

    score = predict(features)

    return {
        "viral_score":score
    }
