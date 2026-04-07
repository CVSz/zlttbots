from __future__ import annotations

import argparse
from pathlib import Path

from agents import (
    AttackAgent,
    DefendAgent,
    FixAgent,
    LearnAgent,
    PRBotAgent,
    ReasonAgent,
    ScanAgent,
    VerifyAgent,
)
from orchestrator import EventBus, Orchestrator


def main() -> int:
    parser = argparse.ArgumentParser(description="Run singularity closed-loop orchestration")
    parser.add_argument("--sarif", required=True, help="Path to SARIF file")
    args = parser.parse_args()

    sarif_text = Path(args.sarif).read_text(encoding="utf-8")
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
    bus.publish("repo.pushed", {"sarif": sarif_text})
    orchestrator.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
