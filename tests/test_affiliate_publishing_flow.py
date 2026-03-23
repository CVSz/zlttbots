from __future__ import annotations

import sys
from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


def load_module(module_name: str, relative_path: str):
    module_path = ROOT / relative_path
    spec = spec_from_file_location(module_name, module_path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_affiliate_connector_payout_ingestion_daily_controller_and_reporting(monkeypatch):
    monkeypatch.setenv("USE_INMEMORY_DB", "1")
    sys.path.insert(0, str(ROOT / "services/arbitrage-engine/src"))

    server = load_module("test_arb_server_integration", "services/arbitrage-engine/src/api/server.py")
    server.MEMORY_STORE.seed_products(
        [
            {"id": "sku-1", "name": "Mouse", "price": 8.0, "source": "shopee"},
            {"id": "sku-2", "name": "Mouse", "price": 25.0, "source": "lazada"},
        ]
    )

    snapshot = server.client.fetch_network_snapshot

    def fake_snapshot(network, auth_token):
        assert auth_token == "x" * 16
        return type(
            "Snapshot",
            (),
            {
                "commissions": [
                    server.ProductCommission(
                        network=network,
                        product_id="sku-2",
                        payout_rate=0.11,
                        currency="usd",
                        fetched_at=datetime.now(timezone.utc),
                    )
                ],
                "orders": [],
                "fetched_at": datetime.now(timezone.utc),
            },
        )()

    monkeypatch.setattr(server.client, "fetch_network_snapshot", fake_snapshot)

    client = TestClient(server.app)

    sync_resp = client.post("/affiliate/sync", json={"network": "lazada", "auth_token": "x" * 16})
    assert sync_resp.status_code == 200
    assert sync_resp.json()["commissions"] == 1

    for idx in range(35):
        enqueue = client.post(
            "/publishing/jobs",
            json={
                "tenant_id": "tenant-a",
                "product_id": "sku-2",
                "video_id": f"video-{idx}",
                "destination_url": "https://example.com/p/sku-2",
            },
        )
        assert enqueue.status_code == 200

    run_resp = client.post(
        "/publishing/run-daily",
        json={
            "tenant_id": "tenant-a",
            "simulation": {"status": "submitted", "external_id": "pub-ok", "network": "lazada"},
        },
    )
    assert run_resp.status_code == 200
    assert run_resp.json()["published"] == 30
    assert run_resp.json()["remaining_capacity"] == 0

    second_run = client.post(
        "/publishing/run-daily",
        json={
            "tenant_id": "tenant-a",
            "simulation": {"status": "submitted", "external_id": "pub-ok", "network": "lazada"},
        },
    )
    assert second_run.status_code == 200
    assert second_run.json()["processed"] == 0

    perf_resp = client.post(
        "/performance",
        json={
            "tenant_id": "tenant-a",
            "product_id": "sku-2",
            "clicks": 12,
            "conversions": 3,
            "revenue": 42.5,
        },
    )
    assert perf_resp.status_code == 200

    report_resp = client.get("/reporting/posted-products/tenant-a")
    assert report_resp.status_code == 200
    rows = report_resp.json()["rows"]
    assert len(rows) == 30
    assert rows[0]["commission_rate"] == 0.11
    assert rows[0]["revenue"] == 42.5
    assert rows[0]["commission_freshness_ts"] is not None

    monkeypatch.setattr(server.client, "fetch_network_snapshot", snapshot)


def test_dead_letter_after_retry_budget(monkeypatch):
    monkeypatch.setenv("USE_INMEMORY_DB", "1")
    sys.path.insert(0, str(ROOT / "services/arbitrage-engine/src"))
    server = load_module("test_arb_server_dead_letter", "services/arbitrage-engine/src/api/server.py")

    client = TestClient(server.app)

    enqueue = client.post(
        "/publishing/jobs",
        json={
            "tenant_id": "tenant-b",
            "product_id": "sku-fail",
            "video_id": "video-fail",
            "destination_url": "https://example.com/fail",
        },
    )
    assert enqueue.status_code == 200

    for _ in range(3):
        run_resp = client.post(
            "/publishing/run-daily",
            json={
                "tenant_id": "tenant-b",
                "simulation": {"status": "failed", "external_id": "pub-fail", "network": "tiktok"},
            },
        )
        assert run_resp.status_code == 200

    report = client.get("/reporting/posted-products/tenant-b")
    assert report.status_code == 200
    assert len(report.json()["dead_letters"]) == 1
