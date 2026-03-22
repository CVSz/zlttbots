from __future__ import annotations

import hashlib
import hmac
import json
import sys
import types
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


class FakeRedis:
    def __init__(self):
        self.store: dict[str, dict[str, str]] = {}

    def ping(self):
        return True

    def hgetall(self, key: str):
        return dict(self.store.get(key, {}))

    def hset(self, key: str, mapping: dict[str, object]):
        current = self.store.setdefault(key, {})
        current.update({field: str(value) for field, value in mapping.items()})
        return 1


def test_feature_store_supports_budget_and_revenue_updates(monkeypatch):
    redis_stub = FakeRedis()
    import redis

    monkeypatch.setattr(redis.Redis, 'from_url', staticmethod(lambda *args, **kwargs: redis_stub))
    module = load_module('test_feature_store_profit', 'services/feature-store/src/main.py')
    client = TestClient(module.app)

    response = client.post('/features/cmp-profit', json={
        'views': 100,
        'clicks': 10,
        'conversions': 2,
        'revenue': 12.5,
        'max_budget': 150,
        'daily_cap': 45,
        'base_bid': 0.35,
    })
    assert response.status_code == 200
    assert response.json() == {
        'views': 100,
        'clicks': 10,
        'conversions': 2,
        'revenue': 12.5,
        'spend': 0.0,
        'max_budget': 150.0,
        'daily_cap': 45.0,
        'base_bid': 0.35,
    }

    latest = client.get('/features/cmp-profit')
    assert latest.status_code == 200
    assert latest.json()['revenue'] == 12.5
    assert latest.json()['max_budget'] == 150.0


def test_affiliate_webhook_updates_feature_store_and_reward_collector(monkeypatch):
    monkeypatch.setenv('AFFILIATE_WEBHOOK_SECRET', 'topsecret')
    calls: list[tuple[str, dict[str, object]]] = []

    class DummyConn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def cursor(self):
            return self

        def execute(self, *args, **kwargs):
            return None

    psycopg_stub = types.SimpleNamespace(connect=lambda *args, **kwargs: DummyConn())
    sys.modules['psycopg2'] = psycopg_stub
    module = load_module('test_affiliate_webhook_profit', 'services/affiliate-webhook/src/main.py')

    def fake_post(url, json=None, timeout=None):
        calls.append((url, json))
        return types.SimpleNamespace(raise_for_status=lambda: None)

    monkeypatch.setattr(module.requests, 'post', fake_post)
    client = TestClient(module.app)
    payload = {'campaign_id': 'cmp-1', 'revenue': 9.5, 'clicks': 3, 'views': 100, 'conversions': 1}
    body = json.dumps(payload).encode('utf-8')
    signature = hmac.new(b'topsecret', body, hashlib.sha256).hexdigest()

    response = client.post('/conversion', content=body, headers={'X-Signature': signature, 'Content-Type': 'application/json'})
    assert response.status_code == 200
    assert calls[0][0].endswith('/features/cmp-1')
    assert calls[0][1]['revenue'] == 9.5
    assert calls[1][0].endswith('/reward')


def test_profit_mode_activation_wires_tracking_payment_and_execution(monkeypatch):
    sys.path.insert(0, str(ROOT / 'services/master-orchestrator/src'))
    sys.modules['distributed_loop'] = types.SimpleNamespace(run_cycle=lambda campaign_id: {
        'features': {'views': 100, 'clicks': 10, 'conversions': 2, 'max_budget': 120, 'daily_cap': 40, 'base_bid': 0.2},
        'rl': {'selected_campaign_id': campaign_id, 'score': 0.82},
        'budget': {'target_budget': 40.0},
        'bid': {'bid_price': 0.7},
        'scale': {'action': 'hold'},
    })
    sys.modules['economy_loop'] = types.SimpleNamespace(run_economy=lambda *args, **kwargs: {'ok': True})
    sys.modules['federated_loop'] = types.SimpleNamespace(run_global_task=lambda *args, **kwargs: {'ok': True})
    emitted: list[dict[str, object]] = []
    sys.modules['kafka_producer'] = types.SimpleNamespace(emit_decision=lambda payload: emitted.append(payload))

    module = load_module('test_master_orchestrator_profit', 'services/master-orchestrator/src/main.py')

    def fake_safe_call(method, url, **kwargs):
        if 'feature-store:8000/features' in url:
            return {'ok': True}
        if 'model-service:8000/predict' in url:
            return {'score': 0.91, 'ctr': 0.1, 'cvr': 0.2, 'model_version': 'policy-v2'}
        if 'execution-engine:9600/publish' in url:
            return {'ok': True, 'status': 'submitted', 'id': 'pub-1'}
        if 'payment-gateway:8000/checkout' in url:
            return {'status': 'pending', 'provider': 'stripe', 'checkout_url': 'https://pay.example/checkout/abc'}
        raise AssertionError(url)

    monkeypatch.setattr(module, 'safe_call', fake_safe_call)
    client = TestClient(module.app)

    response = client.post('/profit-mode/activate', json={
        'campaign_id': 'cmp-77',
        'video_url': 'https://cdn.example/video.mp4',
        'caption': 'Profit mode creative',
        'landing_url': 'https://affiliate.example/product',
        'affiliate_product_id': 'sku-77',
        'tenant_id': 'tenant-a',
        'region': 'us-east',
        'market': 'US',
        'max_budget': 150,
        'daily_cap': 55,
        'base_bid': 0.3,
        'payment': {
            'provider': 'stripe',
            'amount': 49.99,
            'currency': 'usd',
            'success_url': 'https://app.example/success',
            'cancel_url': 'https://app.example/cancel',
        },
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload['tracked_destination_url'].endswith('/go/cmp-77/sku-77')
    assert payload['payment']['provider'] == 'stripe'
    assert emitted[0]['audit']['profit_mode'] is True
