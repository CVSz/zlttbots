import os
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field

from .async_queue import AsyncInferenceProducer, AsyncInferenceUnavailable
from .onnx_model import MODEL_PATH, ONNXModel

app = FastAPI(title="Model Service")
MODEL_VERSION = os.getenv("MODEL_VERSION", "baseline-ctr-cvr-v2-onnx")
ASYNC_INFERENCE_ENABLED = os.getenv("ASYNC_INFERENCE_ENABLED", "false").lower() == "true"
model = ONNXModel(model_path=MODEL_PATH)
async_producer = AsyncInferenceProducer.from_env(enabled=ASYNC_INFERENCE_ENABLED)


class FeatureVector(BaseModel):
    views: int = Field(ge=0)
    clicks: int = Field(ge=0)
    conversions: int = Field(ge=0)


class PredictionResult(BaseModel):
    score: float
    ctr: float
    cvr: float
    model_version: str


class AsyncPredictionQueued(BaseModel):
    job_id: str
    status: str


def featurize(features: FeatureVector) -> list[float]:
    ctr = features.clicks / features.views if features.views else 0.0
    cvr = features.conversions / features.clicks if features.clicks else 0.0
    return [ctr, cvr]


def predict(features: FeatureVector) -> PredictionResult:
    ctr, cvr = featurize(features)
    outputs = model.predict([ctr, cvr])[0]
    score = float(outputs[1]) if len(outputs) > 1 else float(outputs[0])
    return PredictionResult(score=score, ctr=ctr, cvr=cvr, model_version=MODEL_VERSION)


@app.on_event("startup")
def warm_up_model() -> None:
    model.warm_up()


@app.get("/healthz")
def healthz(response: Response) -> dict[str, Any]:
    if not model.ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ok" if model.ready else "degraded",
        "service": "model-service",
        "model_version": MODEL_VERSION,
        "model_path": str(model.model_path),
        "async_inference_enabled": ASYNC_INFERENCE_ENABLED,
    }


@app.post("/predict", response_model=PredictionResult)
def predict_api(features: FeatureVector) -> PredictionResult:
    if not model.ready:
        raise HTTPException(status_code=503, detail=f"ONNX model is unavailable at {model.model_path}")
    return predict(features)


@app.post("/predict_async", response_model=AsyncPredictionQueued, status_code=status.HTTP_202_ACCEPTED)
def predict_async(features: FeatureVector) -> AsyncPredictionQueued:
    if not model.ready:
        raise HTTPException(status_code=503, detail=f"ONNX model is unavailable at {model.model_path}")
    try:
        job_id = async_producer.enqueue(featurize(features))
    except AsyncInferenceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return AsyncPredictionQueued(job_id=job_id, status="queued")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
