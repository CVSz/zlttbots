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


def test_budget_allocator_enforces_step_and_cap() -> None:
    app = _load_app('budget-allocator')
    client = TestClient(app)

    response = client.post(
        '/allocate',
        json={
            'campaign_id': 'cmp-1',
            'score': 0.9,
            'current_spend': 95,
            'max_budget': 100,
            'daily_cap': 98,
            'min_step': 1,
            'max_step': 25,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data['target_budget'] == 88.2
    assert data['adjustment'] == -6.8
    assert data['available_budget'] == 3.0
    assert data['capped'] is False


def test_rtb_engine_clamps_bid_and_applies_pacing() -> None:
    app = _load_app('rtb-engine')
    client = TestClient(app)

    response = client.post(
        '/bid',
        json={
            'campaign_id': 'cmp-1',
            'score': 1.0,
            'ctr': 1.0,
            'cvr': 1.0,
            'base_bid': 2.0,
            'pacing_ratio': 2.0,
            'max_bid': 5.0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data['bid_price'] == 5.0
    assert data['pacing_multiplier'] == 1.5


def test_rl_coordinator_picks_highest_score(monkeypatch) -> None:
    requests_stub = types.SimpleNamespace(post=None, get=None, RequestException=Exception)
    sys.modules['requests'] = requests_stub
    app = _load_app('rl-coordinator')
    client = TestClient(app)

    class DummyResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_post(url, json, timeout):
        if 'rl-agent-1' in url:
            return DummyResponse({'selected_campaign_id': json['campaign_id'], 'score': 0.25, 'arms': [json['campaign_id']]})
        return DummyResponse({'selected_campaign_id': json['campaign_id'], 'score': 0.5, 'arms': [json['campaign_id']]})

    monkeypatch.setattr(sys.modules['requests'], 'post', fake_post)

    response = client.post('/decide', json={'campaign_id': 'cmp-1', 'features': {'views': 10, 'clicks': 2, 'conversions': 1}})
    assert response.status_code == 200
    data = response.json()
    assert data['score'] == 0.5
    assert data['agent'] == 'rl-agent-2:8000'


def test_rtb_engine_applies_latency_penalty() -> None:
    app = _load_app('rtb-engine')
    client = TestClient(app)

    response = client.post(
        '/bid',
        json={
            'campaign_id': 'cmp-latency',
            'score': 0.8,
            'ctr': 0.5,
            'cvr': 0.2,
            'base_bid': 2.0,
            'pacing_ratio': 1.0,
            'max_bid': 10.0,
            'latency_ms': 600.0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data['bid_price'] == 1.8
    assert data['pacing_multiplier'] == 1.0
