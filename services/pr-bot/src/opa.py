from __future__ import annotations

from typing import Any


def evaluate_gate(findings: list[dict[str, Any]]) -> dict[str, list[str]]:
    deny: list[str] = []
    warn: list[str] = []

    for item in findings:
        severity = str(item.get("severity", "")).lower()
        comment = str(item.get("comment", "")).strip()
        if not comment:
            continue
        if severity == "critical":
            deny.append(f"BLOCKER: {comment}")
        elif severity == "medium":
            warn.append(comment)

    return {"deny": deny, "warn": warn}
