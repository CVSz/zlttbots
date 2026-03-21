from __future__ import annotations

import json
import os
from typing import Any

import numpy as np
import ray
from ray import serve

from onnx_model import ONNXModel

RAY_ADDRESS = os.getenv("RAY_ADDRESS", "auto")


@serve.deployment(num_replicas=int(os.getenv("RAY_SERVE_REPLICAS", "2")), ray_actor_options={"num_cpus": 1})
class ModelDeployment:
    def __init__(self) -> None:
        self.model = ONNXModel()

    async def __call__(self, request: Any) -> dict[str, float]:
        payload = await request.json()
        features = np.asarray(payload["features"], dtype=np.float32)
        outputs = self.model.predict(features)
        score = float(outputs[0][1]) if outputs.shape[1] > 1 else float(outputs[0][0])
        return {"score": score}


app = ModelDeployment.bind()


if __name__ == "__main__":
    ray.init(address=RAY_ADDRESS, ignore_reinit_error=True)
    serve.run(app, name="model-service")
    print(json.dumps({"status": "running", "ray_address": RAY_ADDRESS}))
