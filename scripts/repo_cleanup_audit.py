#!/usr/bin/env python3
"""Deterministic repository cleanup audit and quarantine tool.

This tool discovers potentially-unused source files from configured entrypoints.
It supports Python and JavaScript/TypeScript local imports and can quarantine
unreachable files into a single archive folder.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "repo_cleanup_entrypoints.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "feature_repo" / "cleanup_reports"
DEFAULT_QUARANTINE_DIR = REPO_ROOT / "feature_repo" / "unused_candidates"

SOURCE_EXTENSIONS = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx"}
EXCLUDED_PARTS = {
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "__pycache__",
}

PY_IMPORT_RE = re.compile(r"^\s*(?:from\s+([\.\w/]+)\s+import|import\s+([\w\.]+))", re.MULTILINE)
JS_IMPORT_RE = re.compile(
    r"(?:import\s+(?:[^\"']+\s+from\s+)?|require\()\s*[\"']([^\"']+)[\"']",
    re.MULTILINE,
)


@dataclass(frozen=True)
class GraphResult:
    sources: dict[Path, set[Path]]
    reachable: set[Path]
    unreachable: set[Path]
    entrypoints: set[Path]


class ConfigError(ValueError):
    pass


def load_config(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    required = {"include_roots", "entrypoints", "protected_files"}
    missing = required - set(data.keys())
    if missing:
        raise ConfigError(f"Missing config keys: {sorted(missing)}")

    return data


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.parts)


def list_source_files(include_roots: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for rel_root in include_roots:
        root = (REPO_ROOT / rel_root).resolve()
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            rel_path = path.relative_to(REPO_ROOT)
            if is_excluded(rel_path):
                continue
            if path.suffix in SOURCE_EXTENSIONS:
                files.append(path)

    files.sort()
    return files


def candidate_local_module_targets(base_file: Path, spec: str) -> list[Path]:
    base_dir = base_file.parent
    targets: list[Path] = []

    if spec.startswith("."):
        module_path = (base_dir / spec).resolve()
    else:
        return []

    if module_path.suffix:
        targets.append(module_path)
    else:
        for ext in SOURCE_EXTENSIONS:
            targets.append(module_path.with_suffix(ext))
        for ext in SOURCE_EXTENSIONS:
            targets.append(module_path / f"index{ext}")

    return targets


def resolve_python_import(source_file: Path, statement: str) -> list[Path]:
    statement = statement.strip()
    if not statement or (not statement.startswith(".")):
        return []

    dots = len(statement) - len(statement.lstrip("."))
    module_suffix = statement[dots:]

    parent = source_file.parent
    for _ in range(max(1, dots) - 1):
        parent = parent.parent

    if module_suffix:
        module_path = parent / module_suffix.replace(".", os.sep)
    else:
        module_path = parent

    candidates: list[Path] = []
    for ext in SOURCE_EXTENSIONS:
        candidates.append(module_path.with_suffix(ext))
    for ext in SOURCE_EXTENSIONS:
        candidates.append(module_path / f"__init__{ext}")
    for ext in SOURCE_EXTENSIONS:
        candidates.append(module_path / f"index{ext}")

    return candidates


def build_dependency_graph(files: list[Path]) -> dict[Path, set[Path]]:
    file_set = {path.resolve() for path in files}
    graph: dict[Path, set[Path]] = {path.resolve(): set() for path in files}

    for source_file in files:
        resolved_source = source_file.resolve()
        content = source_file.read_text(encoding="utf-8", errors="ignore")

        for py_from, py_import in PY_IMPORT_RE.findall(content):
            statement = py_from or py_import
            for target in resolve_python_import(source_file, statement):
                resolved_target = target.resolve()
                if resolved_target in file_set:
                    graph[resolved_source].add(resolved_target)

        for js_spec in JS_IMPORT_RE.findall(content):
            for target in candidate_local_module_targets(source_file, js_spec):
                resolved_target = target.resolve()
                if resolved_target in file_set:
                    graph[resolved_source].add(resolved_target)

    return graph


def normalize_path_list(paths: Iterable[str], existing_files: set[Path]) -> set[Path]:
    normalized: set[Path] = set()
    for rel in paths:
        candidate = (REPO_ROOT / rel).resolve()
        if candidate in existing_files:
            normalized.add(candidate)
    return normalized


def traverse_reachable(graph: dict[Path, set[Path]], starts: set[Path]) -> set[Path]:
    visited: set[Path] = set()
    stack = list(starts)

    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        stack.extend(graph.get(current, []))

    return visited


def analyze(config: dict) -> GraphResult:
    files = list_source_files(config["include_roots"])
    graph = build_dependency_graph(files)
    all_files = set(graph.keys())

    entrypoints = normalize_path_list(config["entrypoints"], all_files)
    protected = normalize_path_list(config["protected_files"], all_files)

    if not entrypoints:
        raise ConfigError("No valid entrypoints found in config.")

    reachable = traverse_reachable(graph, entrypoints | protected) | protected | entrypoints
    unreachable = all_files - reachable

    return GraphResult(
        sources=graph,
        reachable=reachable,
        unreachable=unreachable,
        entrypoints=entrypoints,
    )


def write_report(result: GraphResult, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "cleanup_audit_report.json"

    payload = {
        "entrypoints": sorted(str(p.relative_to(REPO_ROOT)) for p in result.entrypoints),
        "reachable_count": len(result.reachable),
        "unreachable_count": len(result.unreachable),
        "unreachable_files": sorted(str(p.relative_to(REPO_ROOT)) for p in result.unreachable),
    }

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return report_path


def quarantine_files(unreachable_files: set[Path], quarantine_dir: Path) -> Path:
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    moved_manifest = []

    for abs_path in sorted(unreachable_files):
        rel = abs_path.relative_to(REPO_ROOT)
        destination = quarantine_dir / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(abs_path), str(destination))
        moved_manifest.append(str(rel))

    manifest_path = quarantine_dir / "moved_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump({"moved_files": moved_manifest}, f, indent=2)

    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Repository cleanup analyzer for zlttbots")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Path to JSON config file")
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR, help="Report output directory")
    parser.add_argument(
        "--quarantine-dir",
        type=Path,
        default=DEFAULT_QUARANTINE_DIR,
        help="Quarantine destination for unreachable files",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Move unreachable files to quarantine directory",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    result = analyze(config)
    report_path = write_report(result, args.report_dir)

    print(f"Cleanup report written to: {report_path}")
    print(f"Reachable files: {len(result.reachable)}")
    print(f"Unreachable files: {len(result.unreachable)}")

    if args.apply and result.unreachable:
        manifest_path = quarantine_files(result.unreachable, args.quarantine_dir)
        print(f"Quarantine manifest written to: {manifest_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
