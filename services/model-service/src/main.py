import asyncio
import logging
import os
import json
from contextlib import asynccontextmanager
import time
import uuid
from typing import Any

import uvicorn
from confluent_kafka import Producer
from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from pydantic import BaseModel, Field
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from metrics import ASYNC_REQUESTS_TOTAL, RESULT_LOOKUP_LATENCY
from queue_runtime import REQUEST_TOPIC, start_background_consumers
from result_store import result_store

@asynccontextmanager
async def lifespan(_: FastAPI):
    start_background_consumers(predict_from_payload)
    yield


app = FastAPI(title="Model Service", lifespan=lifespan)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("model-service")
WEIGHTS = torch.tensor([0.3, 0.7], dtype=torch.float32)
MODEL_VERSION = os.getenv("MODEL_VERSION", "baseline-ctr-cvr-v1")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "redpanda:9092")
producer = Producer({"bootstrap.servers": KAFKA_BROKER})


class FeatureVector(BaseModel):
    views: int = Field(ge=0)
    clicks: int = Field(ge=0)
    conversions: int = Field(ge=0)


class PredictionResult(BaseModel):
    score: float
    ctr: float
    cvr: float
    model_version: str


class AsyncJobAccepted(BaseModel):
    job_id: str
    status: str


def predict(features: FeatureVector) -> PredictionResult:
    ctr = features.clicks / features.views if features.views else 0.0
    cvr = features.conversions / features.clicks if features.clicks else 0.0
    return [ctr, cvr]


def predict(features: FeatureVector) -> PredictionResult:
    ctr, cvr = featurize(features)
    outputs = model.predict([ctr, cvr])[0]
    score = float(outputs[1]) if len(outputs) > 1 else float(outputs[0])
    return PredictionResult(score=score, ctr=ctr, cvr=cvr, model_version=MODEL_VERSION)


def predict_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    features = FeatureVector.model_validate(payload)
    return predict(features).model_dump()


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "model-service",
        "model_version": MODEL_VERSION,
        "kafka_broker": KAFKA_BROKER,
    }


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/predict", response_model=PredictionResult)
def predict_api(features: FeatureVector) -> PredictionResult:
    if not model.ready:
        raise HTTPException(status_code=503, detail=f"ONNX model is unavailable at {model.model_path}")
    return predict(features)


@app.post("/predict_async", response_model=AsyncJobAccepted)
def predict_async(
    features: FeatureVector,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> AsyncJobAccepted:
    try:
        job_id = idempotency_key or str(uuid.uuid4())
        result_store.set_result(job_id, {"status": "queued", "model_version": MODEL_VERSION})
        producer.produce(
            REQUEST_TOPIC,
            json.dumps(
                {
                    "job_id": job_id,
                    "features": features.model_dump(),
                    "model_version": MODEL_VERSION,
                }
            ).encode("utf-8"),
        )
        producer.flush()
        ASYNC_REQUESTS_TOTAL.inc()
        return AsyncJobAccepted(job_id=job_id, status="queued")
    except Exception as exc:
        log.exception("Failed to enqueue async prediction")
        raise HTTPException(status_code=500, detail=f"Failed to enqueue async prediction: {exc}") from exc


@app.get("/result/{job_id}")
def fetch_result(job_id: str) -> dict[str, Any]:
    started_at = time.perf_counter()
    result = result_store.get_result(job_id)
    RESULT_LOOKUP_LATENCY.observe(time.perf_counter() - started_at)
    return result or {"job_id": job_id, "status": "pending"}


@app.get("/result/{job_id}/wait")
async def wait_result(job_id: str, timeout: int = 10, poll_interval: float = 0.2) -> dict[str, Any]:
    deadline = asyncio.get_running_loop().time() + max(timeout, 1)
    while True:
        result = result_store.get_result(job_id)
        if result and result.get("status") not in {"queued", "pending"}:
            return result
        if asyncio.get_running_loop().time() >= deadline:
            return {"job_id": job_id, "status": "timeout"}
        await asyncio.sleep(max(poll_interval, 0.05))


@app.websocket("/ws/result/{job_id}")
async def ws_result(websocket: WebSocket, job_id: str) -> None:
    await websocket.accept()
    try:
        while True:
            result = result_store.get_result(job_id)
            if result and result.get("status") not in {"queued", "pending"}:
                await websocket.send_json(result)
                return
            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        return
    finally:
        await websocket.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
