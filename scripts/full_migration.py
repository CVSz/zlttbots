#!/usr/bin/env python3
"""Deterministic, safe repository migration utility.

This script migrates legacy zttato-platform naming to zlttbots across:
- file contents (text files)
- directory and file names

It defaults to dry-run mode and prints a JSON summary.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
}

EXCLUDED_FILES = {
    ".github/workflows/zlttbots-ci.yml",
    "scripts/full_migration.py",
    "scripts/rebrand_zlttbots_to_zlttbots.py",
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
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".php",
}

MAPPING: tuple[tuple[str, str], ...] = (
    (r"zttato-platform", "zlttbots"),
    (r"zttato_platform", "zlttbots"),
    (r"ZTTATO_PLATFORM", "ZLTTBOTS"),
    (r"ZTTATO-PLATFORM", "ZLTTBOTS"),
    (r"ZTTATO", "ZLTTBOTS"),
)


@dataclass(frozen=True)
class FileChange:
    path: str
    replacements: dict[str, int]


@dataclass(frozen=True)
class PathRename:
    old_path: str
    new_path: str


def is_text_candidate(path: Path) -> bool:
    return path.suffix in TEXT_EXTENSIONS or path.name in {
        "Dockerfile",
        "Makefile",
        ".env.example",
        ".gitignore",
    }


def is_excluded(relative_path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in relative_path.parts)


def iter_files(root: Path) -> Iterable[Path]:
    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(root)
        if is_excluded(rel):
            continue
        if str(rel) in EXCLUDED_FILES:
            continue
        if is_text_candidate(file_path):
            yield file_path


def apply_mapping(content: str) -> tuple[str, dict[str, int]]:
    updated = content
    counts: dict[str, int] = {}
    for pattern, replacement in MAPPING:
        updated, count = re.subn(pattern, replacement, updated)
        if count:
            counts[pattern] = counts.get(pattern, 0) + count
    return updated, counts


def migrate_file_contents(root: Path, apply: bool) -> list[FileChange]:
    changes: list[FileChange] = []
    for file_path in iter_files(root):
        original = file_path.read_text(encoding="utf-8", errors="ignore")
        updated, counts = apply_mapping(original)
        if not counts:
            continue

        relative = str(file_path.relative_to(root))
        changes.append(FileChange(path=relative, replacements=counts))
        if apply:
            file_path.write_text(updated, encoding="utf-8")
    return changes


def plan_renames(root: Path) -> list[PathRename]:
    rename_plan: list[PathRename] = []
    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        rel = path.relative_to(root)
        if is_excluded(rel):
            continue
        if str(rel) in EXCLUDED_FILES:
            continue

        old_name = path.name
        new_name = old_name
        for pattern, replacement in MAPPING:
            new_name = re.sub(pattern, replacement, new_name)

        if new_name != old_name:
            rename_plan.append(
                PathRename(
                    old_path=str(path.relative_to(root)),
                    new_path=str(path.with_name(new_name).relative_to(root)),
                )
            )
    return rename_plan


def apply_renames(root: Path, renames: list[PathRename]) -> list[PathRename]:
    applied: list[PathRename] = []
    for rename in renames:
        src = root / rename.old_path
        dst = root / rename.new_path

        if not src.exists() or dst.exists():
            continue

        src.rename(dst)
        applied.append(rename)
    return applied


def run(root: Path, apply: bool) -> dict[str, object]:
    file_changes = migrate_file_contents(root, apply=apply)
    planned_renames = plan_renames(root)
    applied_renames = apply_renames(root, planned_renames) if apply else []

    result = {
        "root": str(root),
        "apply_mode": apply,
        "file_change_count": len(file_changes),
        "file_changes": [
            {"path": change.path, "replacements": change.replacements} for change in file_changes
        ],
        "planned_rename_count": len(planned_renames),
        "planned_renames": [rename.__dict__ for rename in planned_renames],
        "applied_rename_count": len(applied_renames),
        "applied_renames": [rename.__dict__ for rename in applied_renames],
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate zttato-platform tokens to zlttbots safely")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="Repository root to scan")
    parser.add_argument("--apply", action="store_true", help="Apply file edits and renames")
    args = parser.parse_args()

    if not args.root.exists() or not args.root.is_dir():
        raise SystemExit(f"Invalid root directory: {args.root}")

    report = run(args.root.resolve(), apply=args.apply)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
