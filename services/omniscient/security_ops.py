"""Attack simulation, defense deployment, and learning primitives."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class DefenseRule:
    """Defense deployment descriptor."""

    name: str
    action: str


def simulate_attack(url: str) -> list[dict[str, str]]:
    """Run deterministic payload simulation against a target URL descriptor."""
    if not url.startswith(("http://", "https://")):
        raise ValueError("url must start with http:// or https://")

    payloads = [
        "../../etc/passwd",
        "http://169.254.169.254/latest/meta-data/",
        "' OR 1=1 --",
    ]

    results = [
        {"payload": payload, "status": "blocked", "target": url} for payload in payloads
    ]
    LOGGER.info(json.dumps({"event": "simulate_attack", "count": len(results)}))
    return results


def deploy_defense(rule: DefenseRule) -> str:
    """Generate a deterministic deployment message for runtime protection."""
    message = f"Deploying runtime protection: {rule.name}:{rule.action}"
    LOGGER.info(json.dumps({"event": "deploy_defense", "rule": rule.name}))
    return message


def learn(history: list[dict[str, str]]) -> str:
    """Consume historical outcomes and return deterministic model update status."""
    status = "model_updated" if history else "model_noop"
    LOGGER.info(json.dumps({"event": "learn", "status": status, "items": len(history)}))
    return status


def risk_score(severity: float, exploitability: float) -> float:
    """Bounded 0-10 risk scoring function."""
    if severity < 0 or exploitability < 0:
        raise ValueError("severity and exploitability must be non-negative")

    score = severity * exploitability
    return min(round(score, 2), 10.0)
