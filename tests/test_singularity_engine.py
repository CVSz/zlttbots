from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "singularity" / "src"))

from agents import (  # noqa: E402
    AttackAgent,
    DefendAgent,
    FixAgent,
    LearnAgent,
    PRBotAgent,
    ReasonAgent,
    ScanAgent,
    VerifyAgent,
)
from orchestrator import EventBus, Orchestrator  # noqa: E402
from risk import risk  # noqa: E402


def test_singularity_orchestration_generates_verify_event() -> None:
    sarif_payload = {
        "runs": [
            {
                "results": [
                    {"ruleId": "py/ssrf", "level": "error"},
                    {"ruleId": "py/path-injection", "level": "warning"},
                ]
            }
        ]
    }

    bus = EventBus()
    agents = [
        ScanAgent(),
        ReasonAgent(),
        FixAgent(),
        AttackAgent(),
        VerifyAgent(),
        DefendAgent(),
        PRBotAgent(),
        LearnAgent(),
    ]
    orchestrator = Orchestrator(agents=agents, bus=bus)
    bus.publish("repo.pushed", {"sarif": json.dumps(sarif_payload)})
    orchestrator.run()

    events = bus.history()
    topics = [event.topic for event in events]

    assert "verify.done" in topics
    assert any(topic in {"deploy.policy", "patch.revise"} for topic in topics)


def test_risk_score_stable() -> None:
    assert risk(severity=1.0, exploitability=0.8, reachability=0.5) == 8.4
