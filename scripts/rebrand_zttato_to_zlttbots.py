#!/usr/bin/env python3
"""Repository-wide deterministic brand audit and rebrand utility.

Scans text source files for legacy zttato-platform tokens and can optionally
apply in-place replacements to zlttbots naming.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = REPO_ROOT / "feature_repo" / "rebrand" / "zttato_to_zlttbots_report.json"

EXCLUDED_PARTS = {
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".pytest_cache",
    "feature_repo",
}

TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".json",
    ".yaml",
    ".yml",
    ".env",
    ".ini",
    ".cfg",
    ".conf",
    ".sh",
    ".md",
    ".txt",
    ".tf",
    ".rego",
    ".sql",
    ".xml",
    ".toml",
}

REPLACEMENTS = (
    ("zttato-platform", "zlttbots"),
    ("zttato_platform", "zlttbots"),
    ("zttato platform", "zlttbots"),
    ("ZTTATO-PLATFORM", "ZLTTBOTS"),
    ("Zttato-Platform", "Zlttbots"),
    ("Zttato Platform", "Zlttbots"),
    ("zttato", "zlttbots"),
    ("Zttato", "Zlttbots"),
    ("ZTTATO", "ZLTTBOTS"),
)


@dataclass(frozen=True)
class MatchRecord:
    file: str
    token: str
    count: int


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.parts)


def should_scan_file(path: Path) -> bool:
    if "rebrand_zttato_to_zlttbots" in path.name:
        return False
    if path.suffix in TEXT_EXTENSIONS:
        return True
    return path.name in {"Dockerfile", "Makefile", ".env.example", ".gitignore"}


def iter_candidate_files(root: Path) -> Iterable[Path]:
    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(root)
        if is_excluded(rel):
            continue
        if should_scan_file(file_path):
            yield file_path


def apply_replacements(text: str) -> tuple[str, dict[str, int]]:
    current = text
    counts: dict[str, int] = {}

    for old, new in REPLACEMENTS:
        count = current.count(old)
        if count > 0:
            counts[old] = count
            current = current.replace(old, new)

    return current, counts


def audit_and_rebrand(root: Path, apply: bool) -> dict:
    root = root.resolve()
    matches: list[MatchRecord] = []
    changed_files: list[str] = []

    for path in iter_candidate_files(root):
        original = path.read_text(encoding="utf-8", errors="ignore")
        replaced, counts = apply_replacements(original)

        if not counts:
            continue

        rel = str(path.relative_to(root))
        for token, count in sorted(counts.items()):
            matches.append(MatchRecord(file=rel, token=token, count=count))

        if apply and replaced != original:
            path.write_text(replaced, encoding="utf-8")
            changed_files.append(rel)

    payload = {
        "root": str(root),
        "legacy_token_hits": [m.__dict__ for m in matches],
        "legacy_token_hit_count": sum(m.count for m in matches),
        "affected_files": sorted({m.file for m in matches}),
        "affected_file_count": len({m.file for m in matches}),
        "changed_files": sorted(changed_files),
        "changed_file_count": len(changed_files),
        "apply_mode": apply,
    }
    return payload


def write_report(report: dict, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit and rebrand zttato-platform tokens to zlttbots")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="Root folder to scan")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH, help="JSON report output path")
    parser.add_argument("--apply", action="store_true", help="Apply in-place replacements")
    args = parser.parse_args()

    report = audit_and_rebrand(args.root, apply=args.apply)
    write_report(report, args.report)

    print(json.dumps({
        "legacy_token_hit_count": report["legacy_token_hit_count"],
        "affected_file_count": report["affected_file_count"],
        "changed_file_count": report["changed_file_count"],
        "report": str(args.report),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
