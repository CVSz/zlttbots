from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import numpy as np
from confluent_kafka import Consumer

from agent_replicator import Replicator
from compute_market import ComputeMarket
from global_strategy import StrategyOptimizer
from ppo import PPO
from treasury import Treasury

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
market = ComputeMarket()
treasury = Treasury()
strategy = StrategyOptimizer()
replicator = Replicator()

market.register("node-1", capacity=10, price_per_unit=0.8, zone="us-east")
market.register("node-2", capacity=5, price_per_unit=0.4, zone="us-west")


def build_autonomous_snapshot(features: np.ndarray, reward: float) -> dict[str, object]:
    allocation = treasury.allocate(features.tolist(), [0.02] * len(features))
    hedge_amount = treasury.hedge(abs(reward))
    assigned_worker = market.assign({"demand": max(float(np.linalg.norm(features)), 1.0)})
    coordination = strategy.coordinate([reward] * strategy.agents)
    replication = replicator.replicate()
    return {
        "allocation": allocation.round(6).tolist(),
        "hedge_amount": hedge_amount,
        "assigned_worker": assigned_worker.worker_id if assigned_worker else None,
        "coordination": coordination,
        "replication": replication,
    }


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
        snapshot = build_autonomous_snapshot(x, reward)
        MODEL_PATH.write_text(json.dumps({"weights": ppo.w.tolist(), "prob": prob, "autonomous_snapshot": snapshot}))
        log.info("updated policy weights=%s autonomous_snapshot=%s", ppo.w.tolist(), snapshot)


if __name__ == "__main__":
    loop()
