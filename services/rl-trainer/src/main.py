from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import numpy as np
from confluent_kafka import Consumer

from ppo import PPO

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("rl-trainer")
MODEL_PATH = Path("/models/policy.onnx")
consumer = Consumer(
    {
        "bootstrap.servers": "redpanda:9092",
        "group.id": "rl-trainer",
        "auto.offset.reset": "earliest",
    }
)
consumer.subscribe(["inference.response"])
ppo = PPO()


def loop() -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    while True:
        msg = consumer.poll(0.1)
        if msg is None:
            time.sleep(0.1)
            continue
        if msg.error():
            log.warning("kafka error: %s", msg.error())
            continue

        data = json.loads(msg.value().decode())
        x = np.asarray(data.get("features", [0.1, 0.1]), dtype=float)
        reward = float(data.get("reward", 0.0))
        old_prob = float(data.get("prob", 0.5))
        prob = ppo.update(x, reward, old_prob)
        MODEL_PATH.write_text(json.dumps({"weights": ppo.w.tolist(), "prob": prob}))
        log.info("updated policy weights=%s", ppo.w.tolist())


if __name__ == "__main__":
    loop()
