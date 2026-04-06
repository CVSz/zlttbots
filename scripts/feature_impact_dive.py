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

JS_ENDPOINT_RE = re.compile(
    r'\b(?:app|router)\.(get|post|put|patch|delete|options|head)\(\s*[\'"]([^\'"]+)[\'"]',
    flags=re.IGNORECASE,
)
PY_DECORATOR_ENDPOINT_RE = re.compile(
    r'@\w+\.(get|post|put|patch|delete|options|head)\(\s*[\'"]([^\'"]+)[\'"]',
    flags=re.IGNORECASE,
)
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
class RuntimeServiceFeature:
    name: str
    language: str
    api_endpoints: tuple[str, ...]


@dataclass(frozen=True)
class ImpactReport:
    compose_services: tuple[str, ...]
    app_features: tuple[AppFeature, ...]
    runtime_services: tuple[RuntimeServiceFeature, ...]
    documented_features: tuple[ServiceDocFeature, ...]

    @property
    def total_features(self) -> int:
        return (
            len(self.compose_services)
            + len(self.app_features)
            + len(self.runtime_services)
            + len(self.documented_features)
        )


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _extract_endpoint_signatures(content: str, suffix: str) -> tuple[str, ...]:
    found: set[str] = set()
    if suffix in {".js", ".ts"}:
        for method, route in JS_ENDPOINT_RE.findall(content):
            found.add(f"{method.upper()} {route}")
    elif suffix == ".py":
        for method, route in PY_DECORATOR_ENDPOINT_RE.findall(content):
            found.add(f"{method.upper()} {route}")
    return tuple(sorted(found))


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
        src_dir = app_dir / "src"
        if not src_dir.exists():
            continue

        endpoint_signatures: set[str] = set()
        for source_file in sorted(src_dir.rglob("*")):
            if source_file.suffix not in {".ts", ".js", ".py"}:
                continue
            content = source_file.read_text(encoding="utf-8")
            endpoint_signatures.update(_extract_endpoint_signatures(content, source_file.suffix))

        features.append(AppFeature(name=app_dir.name, endpoints=tuple(sorted(endpoint_signatures))))

    return tuple(features)


def extract_runtime_service_features(services_dir: Path) -> tuple[RuntimeServiceFeature, ...]:
    if not services_dir.exists():
        return tuple()

    features: list[RuntimeServiceFeature] = []
    for service_dir in sorted(path for path in services_dir.iterdir() if path.is_dir()):
        src_dir = service_dir / "src"
        if not src_dir.exists():
            continue

        endpoint_signatures: set[str] = set()
        language = "unknown"
        source_files = [path for path in src_dir.rglob("*") if path.suffix in {".py", ".js", ".ts"}]

        for source_file in sorted(source_files):
            if source_file.suffix == ".py":
                language = "python"
            elif source_file.suffix in {".js", ".ts"} and language == "unknown":
                language = "node"

            content = source_file.read_text(encoding="utf-8")
            endpoint_signatures.update(_extract_endpoint_signatures(content, source_file.suffix))

        features.append(
            RuntimeServiceFeature(
                name=service_dir.name,
                language=language,
                api_endpoints=tuple(sorted(endpoint_signatures)),
            )
        )

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
        runtime_services=extract_runtime_service_features(repo_root / "services"),
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
        f"- Runtime service modules discovered: **{len(report.runtime_services)}**\n"
        f"- Service documentation feature specs: **{len(report.documented_features)}**\n"
        f"- Aggregate discovered feature surfaces: **{report.total_features}**\n"
    )

    compose_rows = tuple(report.compose_services)
    app_rows = tuple(
        f"{feature.name} ({len(feature.endpoints)} endpoints): "
        + (", ".join(feature.endpoints) if feature.endpoints else "no HTTP routes found")
        for feature in report.app_features
    )
    runtime_rows = tuple(
        f"{feature.name} [{feature.language}] ({len(feature.api_endpoints)} endpoints): "
        + (", ".join(feature.api_endpoints) if feature.api_endpoints else "no HTTP routes found")
        for feature in report.runtime_services
    )
    doc_rows = tuple(f"{doc.slug}: {doc.title}" for doc in report.documented_features)

    return "\n".join(
        [
            summary,
            _render_section("Compose Service Surface", compose_rows),
            _render_section("Application API Surface", app_rows),
            _render_section("Runtime Service API Surface", runtime_rows),
            _render_section("Documented Product Feature Surface", doc_rows),
            "## Recommended Fixes\n\n"
            "1. Consolidate duplicated feature naming between compose services, runtime services, and docs/services into a single source-of-truth manifest.\n"
            "2. Add this script to CI to detect undocumented apps, runtime modules, or routes drift.\n"
            "3. Review all write endpoints and enforce tenant/auth middleware and schema validation at service level.\n",
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
            "runtime_services": [
                {
                    "name": feature.name,
                    "language": feature.language,
                    "endpoint_count": len(feature.api_endpoints),
                    "endpoints": feature.api_endpoints,
                }
                for feature in report.runtime_services
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
