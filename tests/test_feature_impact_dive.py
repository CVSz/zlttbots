import json
from pathlib import Path

from scripts.feature_impact_dive import (
    AppFeature,
    ImpactReport,
    RuntimeServiceFeature,
    ServiceDocFeature,
    build_surface_manifest,
    format_markdown,
    extract_app_features,
    extract_compose_services,
    extract_documented_features,
    extract_runtime_service_features,
    manifest_to_dict,
    validate_manifest,
    write_manifest,
)


def test_extract_compose_services_reads_services_block(tmp_path: Path) -> None:
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text(
        """
services:
  api:
    image: api:latest
  worker:
    image: worker:latest
networks:
  default:
    driver: bridge
""".strip(),
        encoding="utf-8",
    )

    assert extract_compose_services(compose_file) == ("api", "worker")


def test_extract_app_features_discovers_endpoints_from_multiple_files(tmp_path: Path) -> None:
    app_dir = tmp_path / "apps" / "demo" / "src"
    app_dir.mkdir(parents=True)
    (app_dir / "index.ts").write_text(
        """
app.get('/healthz', handler)
""".strip(),
        encoding="utf-8",
    )
    (app_dir / "routes.ts").write_text(
        """
router.post('/deploy', handler)
""".strip(),
        encoding="utf-8",
    )

    features = extract_app_features(tmp_path / "apps")
    assert len(features) == 1
    assert features[0].name == "demo"
    assert features[0].endpoints == ("GET /healthz", "POST /deploy")


def test_extract_runtime_service_features_supports_python_decorators(tmp_path: Path) -> None:
    src_dir = tmp_path / "services" / "predictor" / "src"
    src_dir.mkdir(parents=True)
    (src_dir / "main.py").write_text(
        """
@app.get('/healthz')
def healthz():
    return {'ok': True}
""".strip(),
        encoding="utf-8",
    )

    features = extract_runtime_service_features(tmp_path / "services")
    assert len(features) == 1
    assert features[0].name == "predictor"
    assert features[0].language == "python"
    assert features[0].api_endpoints == ("GET /healthz",)


def test_extract_documented_features_reads_titles(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs" / "services"
    docs_dir.mkdir(parents=True)
    (docs_dir / "analytics.md").write_text("# Analytics Service\n\nDetails", encoding="utf-8")

    docs = extract_documented_features(docs_dir)
    assert docs[0].slug == "analytics"
    assert docs[0].title == "Analytics Service"


def test_build_surface_manifest_contains_write_endpoint_policy() -> None:
    report = ImpactReport(
        compose_services=("platform",),
        app_features=(AppFeature(name="platform", endpoints=("POST /deploy",)),),
        runtime_services=(),
        documented_features=(ServiceDocFeature(slug="platform", title="Platform"),),
    )

    manifest = build_surface_manifest(report)
    record = manifest.services[0]
    assert record.name == "platform"
    assert record.write_policies[0].endpoint == "POST /deploy"
    assert record.write_policies[0].auth == "required"


def test_validate_manifest_detects_drift(tmp_path: Path) -> None:
    report = ImpactReport(
        compose_services=("platform",),
        app_features=(AppFeature(name="platform", endpoints=("GET /healthz",)),),
        runtime_services=(),
        documented_features=(ServiceDocFeature(slug="platform", title="Platform"),),
    )
    manifest = build_surface_manifest(report)
    manifest_path = tmp_path / "manifest.json"
    write_manifest(manifest, manifest_path)

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["services"][0]["endpoints"] = []
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    errors = validate_manifest(report, manifest_path)
    assert errors


def test_validate_manifest_reports_json_decode_errors(tmp_path: Path) -> None:
    report = ImpactReport(
        compose_services=("platform",),
        app_features=(AppFeature(name="platform", endpoints=("GET /healthz",)),),
        runtime_services=(),
        documented_features=(),
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"services": [}', encoding="utf-8")

    errors = validate_manifest(report, manifest_path)
    assert "manifest JSON decode error" in errors[0]


def test_validate_manifest_rejects_non_string_policy_fields(tmp_path: Path) -> None:
    report = ImpactReport(
        compose_services=("platform",),
        app_features=(AppFeature(name="platform", endpoints=("POST /deploy",)),),
        runtime_services=(),
        documented_features=(),
    )
    manifest = build_surface_manifest(report)
    manifest_path = tmp_path / "manifest.json"
    write_manifest(manifest, manifest_path)

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["services"][0]["write_policies"][0]["schema"] = True
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    errors = validate_manifest(report, manifest_path)
    assert any(".schema must be a string" in error for error in errors)


def test_format_markdown_contains_counts() -> None:
    report = ImpactReport(
        compose_services=("api",),
        app_features=(AppFeature(name="platform", endpoints=("GET /healthz",)),),
        runtime_services=(
            RuntimeServiceFeature(
                name="model-service",
                language="python",
                api_endpoints=("POST /predict",),
            ),
        ),
        documented_features=(ServiceDocFeature(slug="analytics", title="Analytics Service"),),
    )

    manifest = build_surface_manifest(report)
    markdown = format_markdown(report, manifest)
    assert "Compose services discovered: **1**" in markdown
    assert "Application API Surface" in markdown
    assert "Runtime Service API Surface" in markdown
    assert "platform (1 endpoints): GET /healthz" in markdown
    assert "Canonical admin-panel path" in markdown


def test_manifest_to_dict_is_json_serializable() -> None:
    report = ImpactReport(
        compose_services=("api",),
        app_features=(),
        runtime_services=(),
        documented_features=(),
    )
    manifest = build_surface_manifest(report)
    payload = manifest_to_dict(manifest)
    json.dumps(payload)
