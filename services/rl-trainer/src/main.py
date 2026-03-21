from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import numpy as np
from confluent_kafka import Consumer

from causal_rl import doubly_robust
from hierarchical_rl import HierarchicalRL
from long_term_reward import long_term_reward
from meta_learning import MetaLearner
from p2p_agent import P2PAgent
from ppo import PPO
from world_model import WorldModel

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
hrl = HierarchicalRL()
wm = WorldModel()
meta = MetaLearner(lr=ppo.lr)
agent = P2PAgent(ppo.w.tolist())
agent.start_server()
reward_history: list[float] = []


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
        propensity = float(data.get("propensity", old_prob))
        model_pred = float(data.get("model_pred", reward))
        next_state = np.asarray(data.get("next_features", x), dtype=float)
        ltv = float(data.get("ltv", float(np.dot(x, np.asarray([1.2, 0.8])[: x.shape[0]]))))

        decisions = hrl.select(x)
        predicted_next_state = wm.predict_next(x)
        wm.update(x, next_state)

        shaped_reward = long_term_reward(short_term=reward, ltv=ltv)
        counterfactual_reward = doubly_robust(shaped_reward, propensity=propensity, model_pred=model_pred)
        reward_history.append(counterfactual_reward)
        adaptive_lr = meta.adapt(reward_history)

        ppo.lr = adaptive_lr
        prob = ppo.update(x, counterfactual_reward, old_prob)
        hrl.update(x, counterfactual_reward, lr=adaptive_lr)
        agent.weights = ppo.w.tolist()

        MODEL_PATH.write_text(
            json.dumps(
                {
                    "weights": ppo.w.tolist(),
                    "prob": prob,
                    "hierarchical": decisions,
                    "predicted_next_state": predicted_next_state.tolist(),
                    "meta_lr": adaptive_lr,
                    "counterfactual_reward": counterfactual_reward,
                }
            )
        )
        log.info(
            "updated policy weights=%s decisions=%s world_state=%s lr=%s",
            ppo.w.tolist(),
            decisions,
            predicted_next_state.tolist(),
            adaptive_lr,
        )


if __name__ == "__main__":
    loop()
