from __future__ import annotations

import json
import logging
import os
import time
from hashlib import sha256
from pathlib import Path

import numpy as np
from confluent_kafka import Consumer

from agent_replicator import Replicator
from compute_market import ComputeMarket
from global_strategy import StrategyOptimizer
from ppo import PPO
from reward import compute_reward
from treasury import Treasury
from token_engine import ComputeTokenEngine
from civilization import Civilization
from sovereign_identity import build_heartbeat_identity
from autonomy.ai_sre import evaluate as evaluate_sre
from autonomy.p2p import default_envelope
from autonomy.redteam import plan as plan_redteam
from autonomy.simulation import World

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("rl-trainer")
MODEL_PATH = Path("/models/policy.onnx")
MODEL_FILE_MODE = 0o600
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
token_engine = ComputeTokenEngine()
simulation = Civilization()
identity = build_heartbeat_identity()
world = World()

market.register("node-1", capacity=10, price_per_unit=0.8, zone="us-east")
market.register("node-2", capacity=5, price_per_unit=0.4, zone="us-west")


def build_autonomous_snapshot(features: np.ndarray, reward: float) -> dict[str, object]:
    allocation = treasury.allocate(features.tolist(), [0.02] * len(features))
    hedge_amount = treasury.hedge(abs(reward))
    assigned_worker = market.assign({"demand": max(float(np.linalg.norm(features)), 1.0)})
    coordination = strategy.coordinate([reward] * strategy.agents)
    replication = replicator.replicate()
    simulation.step()
    world.step()
    sre_incident = evaluate_sre(lambda: {"cpu": 0.2, "oom": 0.0, "kafka_lag": 10.0})
    redteam_plan = plan_redteam("sandbox")
    p2p_envelope = default_envelope("autonomous-snapshot")
    staked = token_engine.stake("worker-1", 100.0)
    rewarded = token_engine.reward("worker-1", 5.0)
    return {
        "allocation": allocation.round(6).tolist(),
        "hedge_amount": hedge_amount,
        "assigned_worker": assigned_worker.worker_id if assigned_worker else None,
        "coordination": coordination,
        "replication": replication,
        "identity": {
            "did": identity["did"],
            "message_b64": identity["message_b64"],
            "signature_b64": identity["signature_b64"],
            "public_key_b64": identity["public_key_b64"],
        },
        "compute_economy": {"staked": staked, "rewarded": rewarded},
        "civilization": simulation.metrics(),
        "nation_state": world.metrics(),
        "ai_sre": {
            "incident": sre_incident.name if sre_incident else None,
            "severity": sre_incident.severity if sre_incident else None,
        },
        "redteam": redteam_plan,
        "p2p": {
            "topic": p2p_envelope.topic,
            "max_hops": p2p_envelope.max_hops,
            "signed": p2p_envelope.signed,
        },
    }


def _redact_snapshot(snapshot: dict[str, object]) -> dict[str, object]:
    redacted = dict(snapshot)
    identity_payload = snapshot.get("identity")
    if isinstance(identity_payload, dict):
        did = str(identity_payload.get("did", ""))
        redacted["identity"] = {
            "did_sha256": sha256(did.encode("utf-8")).hexdigest(),
            "has_signature": bool(identity_payload.get("signature_b64")),
        }
    return redacted


def _snapshot_fingerprint(snapshot: dict[str, object]) -> str:
    canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(canonical).hexdigest()


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
        prob = ppo.update(x, reward, old_prob)
        snapshot = build_autonomous_snapshot(x, reward)
        safe_snapshot = _redact_snapshot(snapshot)
        persisted_payload = {
            "weights": ppo.w.tolist(),
            "prob": prob,
            "autonomous_snapshot_sha256": _snapshot_fingerprint(safe_snapshot),
            "updated_at": int(time.time()),
        }
        encoded_payload = json.dumps(persisted_payload, sort_keys=True, separators=(",", ":"))
        with os.fdopen(
            os.open(MODEL_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, MODEL_FILE_MODE),
            "w",
            encoding="utf-8",
        ) as handle:
            handle.write(encoded_payload)
        log.info(
            "updated policy weights_sha256=%s autonomous_snapshot_sha256=%s",
            sha256(np.asarray(ppo.w, dtype=float).tobytes()).hexdigest(),
            persisted_payload["autonomous_snapshot_sha256"],
        )


if __name__ == "__main__":
    loop()
