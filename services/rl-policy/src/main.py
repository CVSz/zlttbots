from __future__ import annotations

from typing import Any

import numpy as np
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

from train import train_episode

app = FastAPI(title="RL Policy Trainer")


class TrainingSample(BaseModel):
    ctr: float = Field(default=0.0)
    cvr: float = Field(default=0.0)
    reward: float = Field(default=0.0)


class TrainingRequest(BaseModel):
    samples: list[TrainingSample] = Field(default_factory=list)


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"status": "ok", "service": "rl-policy"}


@app.post("/train")
def train(request: TrainingRequest) -> dict[str, Any]:
    samples = request.samples or [TrainingSample(ctr=0.05, cvr=0.01, reward=0.2)]
    dataset = [(np.array([[sample.ctr, sample.cvr]], dtype=float), sample.reward) for sample in samples]
    path = train_episode(dataset)
    return {"ok": True, "path": path, "samples": len(dataset)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
