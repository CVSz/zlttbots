from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any

from orchestrator import EventBus

log = logging.getLogger("singularity")


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    root_cause: str
    impact: str


class BaseAgent:
    subscriptions: tuple[str, ...] = tuple()

    def handle(self, topic: str, payload: dict[str, Any], bus: EventBus) -> None:
        raise NotImplementedError


class ScanAgent(BaseAgent):
    subscriptions = ("repo.pushed",)

    def handle(self, topic: str, payload: dict[str, Any], bus: EventBus) -> None:
        sarif_text = payload.get("sarif")
        if not isinstance(sarif_text, str) or not sarif_text.strip():
            raise ValueError("sarif payload must include non-empty 'sarif' text")
        bus.publish("sarif.ready", {"sarif": sarif_text})


class ReasonAgent(BaseAgent):
    subscriptions = ("sarif.ready",)

    ROOT_CAUSE_BY_RULE = {
        "py/sql-injection": "unsanitized user input reaches database query",
        "py/path-injection": "path input is not canonicalized",
        "py/ssrf": "outbound URL is not allow-listed",
    }

    IMPACT_BY_RULE = {
        "py/sql-injection": "data exfiltration and data tampering",
        "py/path-injection": "arbitrary file read",
        "py/ssrf": "metadata credential leakage",
    }

    def handle(self, topic: str, payload: dict[str, Any], bus: EventBus) -> None:
        sarif = payload.get("sarif", "")
        parsed = json.loads(sarif)
        findings: list[dict[str, str]] = []
        for run in parsed.get("runs", []):
            for result in run.get("results", []):
                rule = str(result.get("ruleId", "unknown"))
                severity = str(result.get("level", "warning"))
                finding = Finding(
                    rule=rule,
                    severity=severity,
                    root_cause=self.ROOT_CAUSE_BY_RULE.get(rule, "unknown input handling weakness"),
                    impact=self.IMPACT_BY_RULE.get(rule, "security impact requires triage"),
                )
                findings.append(finding.__dict__)
        bus.publish("findings.enriched", {"findings": findings})


class FixAgent(BaseAgent):
    subscriptions = ("findings.enriched",)

    def handle(self, topic: str, payload: dict[str, Any], bus: EventBus) -> None:
        findings = payload.get("findings", [])
        if not isinstance(findings, list):
            raise TypeError("findings must be a list")
        patch_lines: list[str] = []
        for finding in findings:
            rule = str(finding.get("rule", "unknown"))
            patch_lines.append(f"# enforce remediation for {rule}")
        patch = "\n".join(patch_lines)
        bus.publish("patch.generated", {"patch": patch, "finding_count": len(findings)})


class AttackAgent(BaseAgent):
    subscriptions = ("patch.generated",)
    ATTACK_PAYLOADS = (
        "../../etc/passwd",
        "http://169.254.169.254/latest/meta-data/",
        "' OR 1=1 --",
    )

    def handle(self, topic: str, payload: dict[str, Any], bus: EventBus) -> None:
        patch = str(payload.get("patch", ""))
        patch_hash = hashlib.sha256(patch.encode("utf-8")).hexdigest()
        results: list[dict[str, Any]] = []
        for idx, attack_payload in enumerate(self.ATTACK_PAYLOADS):
            selector = int(patch_hash[idx * 2 : idx * 2 + 2], 16)
            blocked = selector % 5 != 0
            results.append({"payload": attack_payload, "blocked": blocked})
        bus.publish("attack.results", {"results": results, "patch": patch})


class VerifyAgent(BaseAgent):
    subscriptions = ("attack.results",)

    def handle(self, topic: str, payload: dict[str, Any], bus: EventBus) -> None:
        results = payload.get("results", [])
        ok = all(bool(item.get("blocked")) for item in results)
        bus.publish("verify.done", {"ok": ok, "patch": payload.get("patch", ""), "results": results})


class DefendAgent(BaseAgent):
    subscriptions = ("verify.done",)

    def handle(self, topic: str, payload: dict[str, Any], bus: EventBus) -> None:
        if payload.get("ok"):
            bus.publish(
                "deploy.policy",
                {
                    "policy": [
                        "block egress to 169.254.169.254/32",
                        "enforce path normalization",
                        "enforce parameterized database queries",
                    ]
                },
            )
        else:
            bus.publish("patch.revise", {"reason": "attack simulation failed", "previous": payload})


class PRBotAgent(BaseAgent):
    subscriptions = ("verify.done",)

    def handle(self, topic: str, payload: dict[str, Any], bus: EventBus) -> None:
        log.info(
            json.dumps(
                {
                    "event": "pr.recommendation",
                    "approved": bool(payload.get("ok")),
                    "result_count": len(payload.get("results", [])),
                }
            )
        )


class LearnAgent(BaseAgent):
    subscriptions = ("verify.done",)

    def handle(self, topic: str, payload: dict[str, Any], bus: EventBus) -> None:
        successful = bool(payload.get("ok"))
        log.info(json.dumps({"event": "learning.update", "success": successful}))
