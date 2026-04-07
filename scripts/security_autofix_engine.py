#!/usr/bin/env python3
"""Deterministic CodeQL SARIF remediation engine.

Reads SARIF files, applies safe text rewrites for known high-signal patterns,
and emits a JSON report for auditing.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Finding:
    rule_id: str
    message: str


@dataclass
class FixResult:
    file_path: str
    rule_id: str
    replacements: int


def _iter_findings(sarif_dir: Path) -> Iterable[Finding]:
    for sarif_file in sorted(sarif_dir.glob("*.sarif")):
        payload = json.loads(sarif_file.read_text(encoding="utf-8"))
        for run in payload.get("runs", []):
            for result in run.get("results", []):
                rule_id = str(result.get("ruleId", ""))
                message = str(result.get("message", {}).get("text", ""))
                if rule_id:
                    yield Finding(rule_id=rule_id, message=message)


def _safe_replace(path: Path, pattern: str, replacement: str, flags: int = 0) -> int:
    if not path.exists():
        return 0
    original = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, original, flags=flags)
    if count > 0 and updated != original:
        path.write_text(updated, encoding="utf-8")
    return count


def apply_repo_fixes(repo_root: Path, findings: list[Finding]) -> list[FixResult]:
    fixes: list[FixResult] = []

    # Map CodeQL rule IDs to deterministic, repository-wide remediations.
    for finding in findings:
        # py/unsafe-deserialization
        if finding.rule_id == "py/unsafe-deserialization":
            for py_file in repo_root.rglob("*.py"):
                count = _safe_replace(
                    py_file,
                    r"yaml\.load\(([^,\n\)]+)\)",
                    r"yaml.safe_load(\1)",
                )
                if count:
                    fixes.append(FixResult(str(py_file.relative_to(repo_root)), finding.rule_id, count))

        # py/requests-disabled-cert-check
        if finding.rule_id == "py/requests-disabled-cert-check":
            for py_file in repo_root.rglob("*.py"):
                count = _safe_replace(
                    py_file,
                    r"verify\s*=\s*False",
                    "verify=True",
                )
                if count:
                    fixes.append(FixResult(str(py_file.relative_to(repo_root)), finding.rule_id, count))

    return fixes


def build_report(findings: list[Finding], fixes: list[FixResult]) -> dict[str, object]:
    return {
        "findings_detected": len(findings),
        "rule_ids_detected": sorted({f.rule_id for f in findings}),
        "fixes_applied": [
            {
                "file": item.file_path,
                "rule_id": item.rule_id,
                "replacements": item.replacements,
            }
            for item in fixes
        ],
        "total_replacements": sum(item.replacements for item in fixes),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply deterministic autofixes for CodeQL SARIF findings")
    parser.add_argument("--sarif-dir", required=True, help="Directory containing SARIF files")
    parser.add_argument("--report-path", required=True, help="Where to write JSON remediation report")
    args = parser.parse_args()

    sarif_dir = Path(args.sarif_dir).resolve()
    repo_root = Path.cwd()

    findings = list(_iter_findings(sarif_dir=sarif_dir))
    fixes = apply_repo_fixes(repo_root=repo_root, findings=findings)

    report = build_report(findings=findings, fixes=fixes)
    Path(args.report_path).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
