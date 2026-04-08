from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np
from sklearn.ensemble import IsolationForest

LOGGER = logging.getLogger("infra_tuner_pipeline")


@dataclass(frozen=True)
class InfraState:
    latency_ms: float
    error_rate: float
    cpu_utilization: float
    memory_utilization: float
    restart_count: float


@dataclass(frozen=True)
class ActionThresholds:
    timeout_seconds: int
    retry_count: int
    min_replicas: int
    max_replicas: int


ALLOWED_ACTIONS = {
    "increase_timeout",
    "increase_retries",
    "scale_up",
    "scale_down",
    "no_op",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train deterministic infra tuning policy")
    parser.add_argument("--input", required=True, type=Path, help="Path to newline-delimited JSON metrics")
    parser.add_argument("--output", required=True, type=Path, help="Path for generated policy JSON")
    parser.add_argument("--anomaly-threshold", default=0.65, type=float)
    return parser.parse_args()


def load_states(path: Path) -> List[InfraState]:
    if not path.exists():
        raise FileNotFoundError(f"metrics input not found: {path}")

    states: List[InfraState] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            row = raw.strip()
            if not row:
                continue
            payload = json.loads(row)
            try:
                states.append(
                    InfraState(
                        latency_ms=float(payload["latency_ms"]),
                        error_rate=float(payload["error_rate"]),
                        cpu_utilization=float(payload["cpu_utilization"]),
                        memory_utilization=float(payload["memory_utilization"]),
                        restart_count=float(payload["restart_count"]),
                    )
                )
            except KeyError as exc:
                raise ValueError(f"missing key at line {line_number}: {exc}") from exc
    if not states:
        raise ValueError("no valid metrics were loaded")
    return states


def to_matrix(states: List[InfraState]) -> np.ndarray:
    matrix = np.array(
        [
            [
                state.latency_ms,
                state.error_rate,
                state.cpu_utilization,
                state.memory_utilization,
                state.restart_count,
            ]
            for state in states
        ],
        dtype=np.float64,
    )
    return matrix


def choose_action(state: InfraState, is_anomaly: bool) -> str:
    if is_anomaly and state.error_rate > 0.05:
        return "increase_retries"
    if is_anomaly and state.latency_ms > 1200:
        return "scale_up"
    if state.cpu_utilization > 0.85 or state.memory_utilization > 0.90:
        return "scale_up"
    if state.cpu_utilization < 0.35 and state.memory_utilization < 0.40 and state.restart_count == 0:
        return "scale_down"
    if state.latency_ms > 800:
        return "increase_timeout"
    return "no_op"


def build_policy(states: List[InfraState], anomaly_threshold: float) -> Dict[str, object]:
    matrix = to_matrix(states)
    forest = IsolationForest(
        n_estimators=200,
        contamination="auto",
        random_state=42,
        n_jobs=1,
    )
    forest.fit(matrix)
    raw_scores = -forest.score_samples(matrix)

    action_counts = {action: 0 for action in ALLOWED_ACTIONS}
    for state, score in zip(states, raw_scores):
        action = choose_action(state, bool(score >= anomaly_threshold))
        action_counts[action] += 1

    dominant_action = max(action_counts, key=action_counts.get)
    thresholds = ActionThresholds(
        timeout_seconds=10 if dominant_action in {"increase_timeout", "increase_retries"} else 5,
        retry_count=10 if dominant_action == "increase_retries" else 6,
        min_replicas=3,
        max_replicas=12 if dominant_action == "scale_up" else 8,
    )

    return {
        "model": "deterministic-isolation-forest-v1",
        "seed": 42,
        "records": len(states),
        "anomaly_threshold": anomaly_threshold,
        "action_counts": action_counts,
        "dominant_action": dominant_action,
        "recommended_thresholds": thresholds.__dict__,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args = parse_args()
    states = load_states(args.input)
    policy = build_policy(states, args.anomaly_threshold)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    LOGGER.info("wrote policy to %s", args.output)


if __name__ == "__main__":
    main()
