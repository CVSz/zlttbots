#!/usr/bin/env python3
"""Generate and validate a deterministic feature inventory for the repository."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "development" / "feature-impact-dive-2026-04-06.md"
DEFAULT_MANIFEST = REPO_ROOT / "config" / "service-surface-manifest.json"

JS_ENDPOINT_RE = re.compile(
    r'\b(?:app|router)\.(get|post|put|patch|delete|options|head)\(\s*[\'\"]([^\'\"]+)[\'\"]',
    flags=re.IGNORECASE,
)
PY_DECORATOR_ENDPOINT_RE = re.compile(
    r'@\w+\.(get|post|put|patch|delete|options|head)\(\s*[\'\"]([^\'\"]+)[\'\"]',
    flags=re.IGNORECASE,
)
DOC_HEADING_RE = re.compile(r"^#\s+(.+?)\s*$")
SERVICE_NAME_RE = re.compile(r"^\s{2}([a-zA-Z0-9_.-]+):\s*$")
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


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


@dataclass(frozen=True)
class EndpointPolicy:
    endpoint: str
    auth: str
    tenant: str
    schema: str


@dataclass(frozen=True)
class ServiceManifestRecord:
    name: str
    compose: bool
    runtime: bool
    app: bool
    docs: bool
    docs_path: str | None
    runtime_language: str | None
    endpoints: tuple[str, ...]
    write_policies: tuple[EndpointPolicy, ...]


@dataclass(frozen=True)
class SurfaceManifest:
    canonical_admin_panel: str
    baseline_runtime_services: tuple[str, ...]
    extended_runtime_services: tuple[str, ...]
    services: tuple[ServiceManifestRecord, ...]


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


def build_surface_manifest(report: ImpactReport) -> SurfaceManifest:
    app_map = {feature.name: feature for feature in report.app_features}
    runtime_map = {feature.name: feature for feature in report.runtime_services}
    docs_map = {feature.slug: feature for feature in report.documented_features}

    all_names = sorted(set(report.compose_services) | set(app_map) | set(runtime_map) | set(docs_map))
    records: list[ServiceManifestRecord] = []

    for name in all_names:
        endpoints = sorted(set(app_map.get(name, AppFeature(name, tuple())).endpoints) | set(runtime_map.get(name, RuntimeServiceFeature(name, "unknown", tuple())).api_endpoints))
        write_policies = tuple(
            EndpointPolicy(endpoint=endpoint, auth="required", tenant="required", schema="required")
            for endpoint in endpoints
            if endpoint.split(" ", maxsplit=1)[0] in WRITE_METHODS
        )
        records.append(
            ServiceManifestRecord(
                name=name,
                compose=name in report.compose_services,
                runtime=name in runtime_map,
                app=name in app_map,
                docs=name in docs_map,
                docs_path=f"docs/services/{name}.md" if name in docs_map else None,
                runtime_language=runtime_map[name].language if name in runtime_map else None,
                endpoints=tuple(endpoints),
                write_policies=write_policies,
            )
        )

    baseline = tuple(
        sorted(
            service
            for service in report.compose_services
            if service
            in {
                "nginx",
                "postgres",
                "redis",
                "viral-predictor",
                "market-crawler",
                "arbitrage-engine",
                "gpu-renderer",
                "tiktok-uploader",
                "analytics",
                "click-tracker",
                "account-farm",
                "ai-video-generator",
                "admin-panel",
            }
        )
    )
    extended = tuple(sorted(service for service in report.compose_services if service not in set(baseline)))

    return SurfaceManifest(
        canonical_admin_panel="nextjs-app-router",
        baseline_runtime_services=baseline,
        extended_runtime_services=extended,
        services=tuple(records),
    )


def manifest_to_dict(manifest: SurfaceManifest) -> dict[str, object]:
    return {
        "canonical_admin_panel": manifest.canonical_admin_panel,
        "baseline_runtime_services": manifest.baseline_runtime_services,
        "extended_runtime_services": manifest.extended_runtime_services,
        "services": [
            {
                **asdict(record),
                "write_policies": [asdict(policy) for policy in record.write_policies],
            }
            for record in manifest.services
        ],
    }


def write_manifest(manifest: SurfaceManifest, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest_to_dict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_manifest(report: ImpactReport, manifest_path: Path) -> list[str]:
    if not manifest_path.exists():
        return [f"manifest not found: {manifest_path}"]

    expected = json.loads(json.dumps(manifest_to_dict(build_surface_manifest(report))))
    actual = json.loads(manifest_path.read_text(encoding="utf-8"))

    errors: list[str] = []
    if expected != actual:
        errors.append("service surface manifest drift detected; run scripts/feature_impact_dive.py --write-manifest")

    return errors


def _render_section(title: str, rows: Iterable[str]) -> str:
    formatted_rows = "\n".join(f"- {row}" for row in rows)
    return f"## {title}\n\n{formatted_rows if formatted_rows else '- (none)'}\n"


def format_markdown(report: ImpactReport, manifest: SurfaceManifest) -> str:
    summary = (
        f"# zTTato Feature Impact Dive\n\n"
        f"- Generated from repository sources on 2026-04-06 (UTC).\n"
        f"- Canonical admin-panel path: **{manifest.canonical_admin_panel}**\n"
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
    policy_rows = tuple(
        f"{record.name}: {len(record.write_policies)} write endpoint policies"
        for record in manifest.services
        if record.write_policies
    )

    return "\n".join(
        [
            summary,
            _render_section("Compose Service Surface", compose_rows),
            _render_section("Application API Surface", app_rows),
            _render_section("Runtime Service API Surface", runtime_rows),
            _render_section("Documented Product Feature Surface", doc_rows),
            _render_section("Write Endpoint Security Policy Surface", policy_rows),
            "## Follow-ups\n\n"
            "1. Keep this report refreshed whenever significant source or dependency changes are merged.\n"
            "2. Expose additional internal services only after documenting auth and ownership.\n"
            "3. Re-run pytest and service-specific frontend builds whenever UI/runtime changes accompany future documentation updates.\n",
        ]
    )


def write_report(report: ImpactReport, manifest: SurfaceManifest, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_markdown(report, manifest), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate repository feature impact dive report")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Markdown output file path")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="Service surface manifest path")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON to stdout")
    parser.add_argument("--write-manifest", action="store_true", help="Write manifest from discovered source-of-truth")
    parser.add_argument("--validate-manifest", action="store_true", help="Validate discovered surface against committed manifest")
    args = parser.parse_args()

    report = build_impact_report(REPO_ROOT)
    manifest = build_surface_manifest(report)
    write_report(report, manifest, args.output)

    if args.write_manifest:
        write_manifest(manifest, args.manifest)

    if args.validate_manifest:
        errors = validate_manifest(report, args.manifest)
        if errors:
            for error in errors:
                print(error)
            return 1

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
            "documented_features": [{"slug": doc.slug, "title": doc.title} for doc in report.documented_features],
            "manifest": manifest_to_dict(manifest),
            "total_features": report.total_features,
        }
        print(json.dumps(payload, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
