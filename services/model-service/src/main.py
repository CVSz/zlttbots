import asyncio
import importlib.util
import json
import logging
import os
from pathlib import Path
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

import torch
from confluent_kafka import Producer
from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from pydantic import BaseModel, Field
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from onnx_model import ONNXModel
from queue_runtime import REQUEST_TOPIC, start_background_consumers
from result_store import result_store


def _load_local_metrics_module():
    module_path = Path(__file__).with_name("metrics.py")
    spec = importlib.util.spec_from_file_location("model_service_metrics", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load metrics module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_metrics = _load_local_metrics_module()
ASYNC_REQUESTS_TOTAL = _metrics.ASYNC_REQUESTS_TOTAL
RESULT_LOOKUP_LATENCY = _metrics.RESULT_LOOKUP_LATENCY

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("model-service")
WEIGHTS = torch.tensor([0.3, 0.7], dtype=torch.float32)
MODEL_VERSION = os.getenv("MODEL_VERSION", "baseline-ctr-cvr-v1")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "redpanda:9092")
producer = Producer({"bootstrap.servers": KAFKA_BROKER})
model = ONNXModel()


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


@asynccontextmanager
async def lifespan(_: FastAPI):
    start_background_consumers(predict_from_payload)
    yield


app = FastAPI(title="Model Service", lifespan=lifespan)


def featurize(features: FeatureVector) -> tuple[float, float]:
    ctr = features.clicks / features.views if features.views else 0.0
    cvr = features.conversions / features.clicks if features.clicks else 0.0
    return ctr, cvr


def fallback_predict(ctr: float, cvr: float) -> float:
    vector = torch.tensor([ctr, cvr], dtype=torch.float32)
    score = torch.dot(WEIGHTS, vector).item()
    return float(max(0.0, min(score, 1.0)))


def predict(features: FeatureVector) -> PredictionResult:
    ctr, cvr = featurize(features)
    if model.ready:
        outputs = model.predict([ctr, cvr])[0]
        score = float(outputs[1]) if len(outputs) > 1 else float(outputs[0])
    else:
        score = fallback_predict(ctr, cvr)
    return PredictionResult(score=score, ctr=ctr, cvr=cvr, model_version=MODEL_VERSION)


def predict_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    raw_features = payload.get("features", payload)
    features = FeatureVector.model_validate(raw_features)
    result = predict(features).model_dump()
    if "job_id" in payload:
        result_store.set_result(payload["job_id"], {"status": "completed", **result})
    return result


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "model-service",
        "model_version": MODEL_VERSION,
        "kafka_configured": bool(KAFKA_BROKER),
        "onnx_ready": model.ready,
    }


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/predict", response_model=PredictionResult)
def predict_api(features: FeatureVector) -> PredictionResult:
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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
