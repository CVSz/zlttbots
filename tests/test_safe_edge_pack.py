from pathlib import Path


def test_tunnel_config_contains_expected_hosts():
    text = Path("infrastructure/cloudflare/tunnel-config.example.yml").read_text()
    for hostname in [
        "api.zeaz.dev",
        "admin.zeaz.dev",
        "auth.zeaz.dev",
        "ai.zeaz.dev",
        "crawl.zeaz.dev",
        "predict.zeaz.dev",
        "grafana.zeaz.dev",
        "kafka.zeaz.dev",
    ]:
        assert hostname in text


def test_kong_config_exposes_summary_and_redirect_routes():
    text = Path("infrastructure/kong/kong.yml").read_text()
    assert "/analytics" in text
    assert "/go" in text
    assert "/r" in text


def test_go_live_doc_has_safety_note():
    text = Path("docs/operations/go-live-safe-edge.md").read_text()
    assert "Do not use it to automate account creation" in text


def test_global_tunnel_config_supports_wildcard_host():
    text = Path("cloudflare-devops/tunnel/config.yml").read_text()
    assert "*.zeaz.dev" in text


def test_global_deploy_script_includes_multi_region_and_worker_steps():
    text = Path("scripts/deploy-global.sh").read_text()
    assert "infrastructure/k8s/multi-region/asia.yaml" in text
    assert "infrastructure/k8s/multi-region/eu.yaml" in text
    assert "wrangler deploy" in text
