#!/usr/bin/env python3
"""Generate a deterministic feature inventory and impact report for the repository."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "development" / "feature-impact-dive-2026-04-06.md"

SERVICE_DOCS_DIR = REPO_ROOT / "docs" / "services"
APPS_DIR = REPO_ROOT / "apps"
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"

ENDPOINT_RE = re.compile(r'app\.(?:get|post|put|patch|delete)\(\s*[\'"]([^\'"]+)[\'"]')
DOC_HEADING_RE = re.compile(r"^#\s+(.+?)\s*$")
SERVICE_NAME_RE = re.compile(r"^\s{2}([a-zA-Z0-9_.-]+):\s*$")


@dataclass(frozen=True)
class AppFeature:
    name: str
    endpoints: tuple[str, ...]


@dataclass(frozen=True)
class ServiceDocFeature:
    slug: str
    title: str


@dataclass(frozen=True)
class ImpactReport:
    compose_services: tuple[str, ...]
    app_features: tuple[AppFeature, ...]
    documented_features: tuple[ServiceDocFeature, ...]

    @property
    def total_features(self) -> int:
        return len(self.compose_services) + len(self.app_features) + len(self.documented_features)


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def extract_compose_services(compose_file: Path) -> tuple[str, ...]:
    if not compose_file.exists():
        return tuple()

    lines = _read_lines(compose_file)
    in_services_block = False
    services: list[str] = []

    for line in lines:
        if not in_services_block:
            if line.strip() == "services:":
                in_services_block = True
            continue

        if line and not line.startswith(" "):
            break

        match = SERVICE_NAME_RE.match(line)
        if match:
            services.append(match.group(1))

    return tuple(sorted(set(services)))


def extract_app_features(apps_dir: Path) -> tuple[AppFeature, ...]:
    if not apps_dir.exists():
        return tuple()

    features: list[AppFeature] = []
    for app_dir in sorted(path for path in apps_dir.iterdir() if path.is_dir()):
        index_file = app_dir / "src" / "index.ts"
        if not index_file.exists():
            continue

        content = index_file.read_text(encoding="utf-8")
        endpoints = tuple(sorted(set(ENDPOINT_RE.findall(content))))
        features.append(AppFeature(name=app_dir.name, endpoints=endpoints))

    return tuple(features)


def extract_documented_features(service_docs_dir: Path) -> tuple[ServiceDocFeature, ...]:
    if not service_docs_dir.exists():
        return tuple()

    docs: list[ServiceDocFeature] = []
    for doc_file in sorted(service_docs_dir.glob("*.md")):
        heading = doc_file.stem.replace("-", " ").title()
        for line in _read_lines(doc_file):
            match = DOC_HEADING_RE.match(line)
            if match:
                heading = match.group(1).strip()
                break
        docs.append(ServiceDocFeature(slug=doc_file.stem, title=heading))

    return tuple(docs)


def build_impact_report(repo_root: Path = REPO_ROOT) -> ImpactReport:
    return ImpactReport(
        compose_services=extract_compose_services(repo_root / "docker-compose.yml"),
        app_features=extract_app_features(repo_root / "apps"),
        documented_features=extract_documented_features(repo_root / "docs" / "services"),
    )


def _render_section(title: str, rows: Iterable[str]) -> str:
    formatted_rows = "\n".join(f"- {row}" for row in rows)
    return f"## {title}\n\n{formatted_rows if formatted_rows else '- (none)'}\n"


def format_markdown(report: ImpactReport) -> str:
    summary = (
        f"# zTTato Feature Impact Dive\n\n"
        f"- Generated from repository sources on 2026-04-06 (UTC).\n"
        f"- Compose services discovered: **{len(report.compose_services)}**\n"
        f"- Node app features discovered: **{len(report.app_features)}**\n"
        f"- Service documentation feature specs: **{len(report.documented_features)}**\n"
        f"- Aggregate discovered feature surfaces: **{report.total_features}**\n"
    )

    compose_rows = tuple(report.compose_services)
    app_rows = tuple(
        f"{feature.name} ({len(feature.endpoints)} endpoints): "
        + (", ".join(feature.endpoints) if feature.endpoints else "no HTTP routes found")
        for feature in report.app_features
    )
    doc_rows = tuple(f"{doc.slug}: {doc.title}" for doc in report.documented_features)

    return "\n".join(
        [
            summary,
            _render_section("Compose Service Surface", compose_rows),
            _render_section("Application API Surface", app_rows),
            _render_section("Documented Product Feature Surface", doc_rows),
            "## Recommended Fixes\n\n"
            "1. Consolidate duplicated feature naming between compose services and docs/services into a single source-of-truth manifest.\n"
            "2. Add this script to CI to detect undocumented apps or routes drift.\n"
            "3. Review app routes that expose write endpoints and enforce tenant/auth middleware at service level.\n",
        ]
    )


def write_report(report: ImpactReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_markdown(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate repository feature impact dive report")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Markdown output file path",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON to stdout",
    )
    args = parser.parse_args()

    report = build_impact_report(REPO_ROOT)
    write_report(report, args.output)

    if args.json:
        payload = {
            "compose_services": report.compose_services,
            "app_features": [
                {
                    "name": feature.name,
                    "endpoint_count": len(feature.endpoints),
                    "endpoints": feature.endpoints,
                }
                for feature in report.app_features
            ],
            "documented_features": [
                {"slug": doc.slug, "title": doc.title} for doc in report.documented_features
            ],
            "total_features": report.total_features,
        }
        print(json.dumps(payload, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
