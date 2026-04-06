from pathlib import Path

from scripts.feature_impact_dive import (
    extract_app_features,
    extract_compose_services,
    extract_documented_features,
    format_markdown,
    ImpactReport,
    AppFeature,
    ServiceDocFeature,
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


def test_extract_app_features_discovers_endpoints(tmp_path: Path) -> None:
    app_dir = tmp_path / "apps" / "demo" / "src"
    app_dir.mkdir(parents=True)
    (app_dir / "index.ts").write_text(
        """
app.get('/healthz', handler)
app.post('/deploy', handler)
""".strip(),
        encoding="utf-8",
    )

    features = extract_app_features(tmp_path / "apps")
    assert len(features) == 1
    assert features[0].name == "demo"
    assert features[0].endpoints == ("/deploy", "/healthz")


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
        app_features=(AppFeature(name="platform", endpoints=("/healthz",)),),
        documented_features=(ServiceDocFeature(slug="analytics", title="Analytics Service"),),
    )

    markdown = format_markdown(report)
    assert "Compose services discovered: **1**" in markdown
    assert "Application API Surface" in markdown
    assert "platform (1 endpoints): /healthz" in markdown
