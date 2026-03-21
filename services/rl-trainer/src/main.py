from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import numpy as np
from confluent_kafka import Consumer

from ppo import PPO
from hybrid_rl import HybridRL
from reward import compute_reward

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
hybrid = HybridRL()


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
        reward = compute_reward(
            revenue=float(data.get("revenue", data.get("reward", 0.0))),
            cost=float(data.get("cost", 0.0)),
            risk=float(data.get("risk", 0.0)),
        )
        old_prob = float(data.get("prob", 0.5))
        arm = hybrid.select_arm(x)
        hybrid.update(arm, reward, x)
        prob = ppo.update(x, reward, old_prob)
        MODEL_PATH.write_text(json.dumps({"weights": ppo.w.tolist(), "prob": prob}))
        log.info("updated policy weights=%s arm=%s hybrid_values=%s", ppo.w.tolist(), arm, hybrid.values.tolist())


if __name__ == "__main__":
    loop()
