import os
from typing import Any

import torch
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Model Service")
WEIGHTS = torch.tensor([0.3, 0.7], dtype=torch.float32)
MODEL_VERSION = os.getenv("MODEL_VERSION", "baseline-ctr-cvr-v1")


class FeatureVector(BaseModel):
    views: int = Field(ge=0)
    clicks: int = Field(ge=0)
    conversions: int = Field(ge=0)


class PredictionResult(BaseModel):
    score: float
    ctr: float
    cvr: float
    model_version: str


def predict(features: FeatureVector) -> PredictionResult:
    ctr = features.clicks / features.views if features.views else 0.0
    cvr = features.conversions / features.clicks if features.clicks else 0.0
    vector = torch.tensor([ctr, cvr], dtype=torch.float32)
    score = float(torch.dot(WEIGHTS, vector).item())
    return PredictionResult(score=score, ctr=ctr, cvr=cvr, model_version=MODEL_VERSION)


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"status": "ok", "service": "model-service", "model_version": MODEL_VERSION}


@app.post("/predict", response_model=PredictionResult)
def predict_api(features: FeatureVector) -> PredictionResult:
    return predict(features)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
