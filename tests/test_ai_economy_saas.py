import sys
import types
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


def _load_app(service: str):
    module_path = ROOT / 'services' / service / 'src' / 'main.py'
    spec = spec_from_file_location(f"{service.replace('-', '_')}_main", module_path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app


def test_product_generator_is_deterministic() -> None:
    app = _load_app('product-generator')
    client = TestClient(app)

    payload = {'tenant_id': 7, 'niche': 'fitness', 'market': 'US'}
    first = client.post('/generate', json=payload)
    second = client.post('/generate', json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()['product_id'] == second.json()['product_id']
    assert first.json()['landing_url'].endswith(first.json()['product_id'])


def test_billing_service_rates_by_plan() -> None:
    app = _load_app('billing-service')
    client = TestClient(app)

    response = client.post('/charge', json={'tenant_id': 3, 'plan': 'growth', 'usage': 250})
    assert response.status_code == 200
    assert response.json()['cost'] == 2.5


def test_market_orchestrator_launches_supported_markets(monkeypatch) -> None:
    requests_stub = types.SimpleNamespace(post=None, RequestException=Exception)
    sys.modules['requests'] = requests_stub
    app = _load_app('market-orchestrator')
    client = TestClient(app)

    class DummyResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_post(url, json, timeout):
        return DummyResponse({'product_id': f"{json['market']}-id", 'market': json['market']})

    monkeypatch.setattr(sys.modules['requests'], 'post', fake_post)

    response = client.post('/launch', json={'tenant_id': 1, 'niche': 'finance', 'markets': ['US', 'EU']})
    assert response.status_code == 200
    assert [item['market'] for item in response.json()['launch']] == ['US', 'EU']


def test_master_orchestrator_economy_endpoint(monkeypatch) -> None:
    requests_stub = types.SimpleNamespace(post=None, get=None, RequestException=Exception)
    sys.modules['requests'] = requests_stub
    sys.modules['confluent_kafka'] = types.SimpleNamespace(Producer=lambda *args, **kwargs: types.SimpleNamespace(produce=lambda *a, **k: None, flush=lambda *a, **k: None))
    sys.path.insert(0, str(ROOT / 'services' / 'master-orchestrator' / 'src'))
    app = _load_app('master-orchestrator')
    client = TestClient(app)

    class DummyResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_get(url, timeout):
        assert 'feature-store' in url
        return DummyResponse({'views': 50, 'clicks': 10, 'conversions': 2, 'spend': 10, 'max_budget': 100, 'daily_cap': 50, 'base_bid': 0.5})

    def fake_post(url, json, timeout, **kwargs):
        if 'market-orchestrator' in url:
            return DummyResponse({'launch': [{'market': 'US', 'product': {'product_id': 'prod-1'}}]})
        if 'rl-coordinator' in url:
            return DummyResponse({'selected_campaign_id': json['campaign_id'], 'score': 0.9})
        if 'budget-allocator' in url:
            return DummyResponse({'target_budget': 35, 'adjustment': 25, 'available_budget': 40, 'capped': False})
        if 'rtb-engine' in url:
            return DummyResponse({'bid_price': 1.23, 'pacing_multiplier': 1.0})
        if 'scaling-engine' in url:
            return DummyResponse({'desired_replicas': 2})
        if 'billing-service' in url:
            return DummyResponse({'cost': 0.5, 'currency': 'USD'})
        raise AssertionError(url)

    monkeypatch.setattr(sys.modules['requests'], 'get', fake_get)
    monkeypatch.setattr(sys.modules['requests'], 'post', fake_post)

    response = client.post('/economy/run', json={'tenant_id': 9, 'niche': 'ai agents', 'markets': ['US']})
    assert response.status_code == 200
    payload = response.json()
    assert payload['tenant_id'] == 9
    assert payload['economy'][0]['cycle']['budget']['target_budget'] == 35
    assert payload['economy'][0]['billing']['cost'] == 0.5
