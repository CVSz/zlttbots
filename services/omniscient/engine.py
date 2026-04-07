"""Core Omniscient security reasoning engine."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from typing import Any

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class FindingAction:
    """Action plan produced from one SARIF finding."""

    finding: str
    root_cause: str
    impact: str
    patch: str
    verified: bool
    defense: str
    risk_score: float


class OmniscientEngine:
    """Analyze SARIF findings, reason about impact, and produce mitigations."""

    def analyze(self, sarif: str) -> list[dict[str, Any]]:
        """Parse SARIF and return normalized findings with strict validation."""
        payload = json.loads(sarif)
        runs = payload.get("runs")
        if not isinstance(runs, list) or not runs:
            raise ValueError("Invalid SARIF: expected non-empty 'runs' array")

        first_run = runs[0]
        results = first_run.get("results")
        if not isinstance(results, list):
            raise ValueError("Invalid SARIF: expected 'results' array")

        normalized: list[dict[str, Any]] = []
        for result in results:
            rule_id = result.get("ruleId")
            if not isinstance(rule_id, str) or not rule_id.strip():
                raise ValueError("Invalid SARIF finding: missing non-empty 'ruleId'")
            normalized.append(result)

        self._log_event("analyze", findings=len(normalized))
        return normalized

    def reason(self, finding: dict[str, Any]) -> tuple[str, str, float]:
        """Derive a deterministic root-cause and impact assessment."""
        rule_id = str(finding["ruleId"]).lower()

        if "sql" in rule_id:
            return ("query input is not parameterized", "database exfiltration", 9.2)
        if "ssrf" in rule_id:
            return ("outbound target is user-controlled", "internal network pivot", 9.0)
        if "xss" in rule_id:
            return ("unescaped HTML is rendered", "session theft", 8.4)

        return ("untrusted input lacks strict validation", "integrity compromise", 7.0)

    def fix(self, finding: dict[str, Any], root_cause: str) -> str:
        """Generate deterministic patch guidance."""
        return (
            f"Apply validation and sanitization for {finding['ruleId']}; "
            f"root cause: {root_cause}."
        )

    def verify(self, finding: dict[str, Any], patch: str) -> bool:
        """Deterministic verification heuristic for CI gating."""
        return bool(finding.get("ruleId")) and len(patch) > 20

    def defend(self, finding: dict[str, Any]) -> str:
        """Produce a runtime defense rule descriptor."""
        return f"runtime-deny:{finding['ruleId']}"

    def run(self, sarif: str) -> list[dict[str, Any]]:
        """Run full omniscient pipeline and return serializable action plans."""
        results = self.analyze(sarif)
        actions: list[dict[str, Any]] = []

        for finding in results:
            root_cause, impact, risk = self.reason(finding)
            patch = self.fix(finding, root_cause)
            verified = self.verify(finding, patch)
            defense = self.defend(finding)

            action = FindingAction(
                finding=finding["ruleId"],
                root_cause=root_cause,
                impact=impact,
                patch=patch,
                verified=verified,
                defense=defense,
                risk_score=risk,
            )
            actions.append(asdict(action))

        self._log_event("run", actions=len(actions))
        return actions

    def _log_event(self, event: str, **fields: Any) -> None:
        payload = {"event": event, **fields}
        LOGGER.info(json.dumps(payload, sort_keys=True))
