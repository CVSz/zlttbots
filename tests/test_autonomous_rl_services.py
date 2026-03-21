import sys
import types

import pytest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


def _load_module(module_name: str, relative_path: str):
    module_path = ROOT / relative_path
    spec = spec_from_file_location(module_name, module_path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_app(service: str):
    return _load_module(f"test_{service.replace('-', '_')}_main", f"services/{service}/src/main.py").app


def test_model_registry_registers_and_returns_latest(tmp_path):
    model_dir = tmp_path / 'models'
    model_dir.mkdir()
    source = tmp_path / 'policy.pt'
    source.write_bytes(b'model-bytes')

    module = _load_module('test_model_registry_main', 'services/model-registry/src/main.py')
    module.BASE = model_dir
    module.SHARED = tmp_path / 'shared'
    module.SHARED.mkdir()
    client = TestClient(module.app)

    response = client.post('/register', json={'name': 'policy', 'version': '100', 'path': str(source)})
    assert response.status_code == 200
    assert (model_dir / 'policy_100.pt').read_bytes() == b'model-bytes'

    latest = client.get('/latest/policy')
    assert latest.status_code == 200
    assert latest.json() == {'model': 'policy_100.pt'}


def test_reward_collector_clips_profit_reward(monkeypatch):
    kafka_stub = types.SimpleNamespace(emit_feedback=lambda payload: payload)
    sys.modules['kafka_producer'] = kafka_stub
    module = _load_module('test_reward_collector_main', 'services/reward-collector/src/main.py')
    client = TestClient(module.app)

    def fake_safe_call(method, url, **kwargs):
        if 'feature-store' in url:
            return {'views': 10, 'clicks': 5, 'conversions': 1}
        return {'ok': True}

    monkeypatch.setattr(module, 'safe_call', fake_safe_call)

    response = client.post('/reward', json={'campaign_id': 'cmp-1', 'revenue': 3.0, 'clicks': 10, 'views': 100, 'conversions': 1})
    assert response.status_code == 200
    assert response.json()['reward'] == 1.0


def test_rl_engine_uses_policy_model_when_present(tmp_path, monkeypatch):
    pytest.importorskip("numpy")
    sys.path.insert(0, str(ROOT / 'services/rl-engine/src'))
    _load_module('policy_model', 'services/rl-engine/src/policy_model.py')
    module = _load_module('test_rl_engine_main', 'services/rl-engine/src/main.py')

    import numpy as np

    class DummyPolicy:
        def eval(self):
            return self

        def __call__(self, vector):
            return np.array([[0.1, 0.9]], dtype=float)

    monkeypatch.setattr(module, 'load_policy_model', lambda: DummyPolicy())
    monkeypatch.setattr(module, 'load_agent', lambda arms: types.SimpleNamespace(arms=arms, select=lambda vector: (arms[0], 0.2)))
    monkeypatch.setattr(module, 'persist_agent', lambda agent: None)
    monkeypatch.setattr(module, 'log_decision', lambda **kwargs: None)

    client = TestClient(module.app)
    response = client.post('/select', json={'campaign_id': 'cmp-1', 'features': {'views': 100, 'clicks': 10, 'conversions': 2}})
    assert response.status_code == 200
    data = response.json()
    assert data['selected_campaign_id'] == 'cmp-1'
    assert data['score'] == 0.9


def test_budget_allocator_exposes_market_budget():
    sys.path.insert(0, str(ROOT / 'services/budget-allocator/src'))
    module = _load_module('test_budget_allocator_main', 'services/budget-allocator/src/main.py')
    client = TestClient(module.app)

    response = client.post('/allocate', json={
        'campaign_id': 'cmp-1',
        'market': 'TH',
        'score': 0.8,
        'current_spend': 20.0,
        'max_budget': 100.0,
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload['market_budget'] > 0
    assert payload['campaign_id'] == 'cmp-1'


def test_rtb_engine_uses_floor_bid():
    sys.path.insert(0, str(ROOT / 'services/rtb-engine/src'))
    module = _load_module('test_rtb_engine_main', 'services/rtb-engine/src/main.py')
    client = TestClient(module.app)

    response = client.post('/bid', json={
        'campaign_id': 'cmp-1',
        'score': 0.5,
        'ctr': 0.0,
        'cvr': 0.0,
        'base_bid': 0.5,
        'pacing_ratio': 1.0,
        'max_bid': 2.0,
        'latency_ms': 120.0,
    })
    assert response.status_code == 200
    assert response.json()['bid_price'] >= 0.01


def test_tlearner_predicts_uplift():
    pytest.importorskip('sklearn')
    module = _load_module('test_uplift_model', 'services/rl-trainer/src/uplift_model.py')
    learner = module.TLearner()
    import numpy as np
    X = np.array([[0.1, 0.2], [0.2, 0.1], [0.8, 0.7], [0.9, 0.6]])
    treatment = np.array([0, 0, 1, 1])
    y = np.array([0, 0, 1, 1])
    learner.fit(X, treatment, y)
    uplift = learner.predict_uplift(np.array([[0.85, 0.65]]))
    assert uplift.shape == (1,)
