from pathlib import Path

from scripts.feature_impact_dive import (
    AppFeature,
    ImpactReport,
    RuntimeServiceFeature,
    ServiceDocFeature,
    extract_app_features,
    extract_compose_services,
    extract_documented_features,
    extract_runtime_service_features,
    format_markdown,
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

    markdown = format_markdown(report)
    assert "Compose services discovered: **1**" in markdown
    assert "Application API Surface" in markdown
    assert "Runtime Service API Surface" in markdown
    assert "platform (1 endpoints): GET /healthz" in markdown
