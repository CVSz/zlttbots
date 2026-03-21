import sys
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


def test_rtb_engine_openrtb_and_reward_fields() -> None:
    module = _load_module('test_rtb_advanced_main', 'services/rtb-engine/src/main.py')
    client = TestClient(module.app)

    bid_response = client.post(
        '/bid',
        json={
            'campaign_id': 'cmp-adv',
            'score': 0.9,
            'ctr': 0.4,
            'cvr': 0.2,
            'base_bid': 1.5,
            'pacing_ratio': 1.2,
            'max_bid': 3.0,
            'revenue': 2.5,
            'propensity': 0.5,
            'model_pred': 0.1,
        },
    )
    assert bid_response.status_code == 200
    payload = bid_response.json()
    assert set(payload['hierarchical_decisions']) == {'campaign', 'adset', 'creative'}
    assert payload['ltv'] == 0.64
    assert 'counterfactual_reward' in payload

    openrtb_response = client.post(
        '/openrtb/bid',
        json={'id': 'req-1', 'imp': [{'id': 'imp-1'}], 'device': {'ua': 'ua'}, 'user': {'id': 'user-1'}},
    )
    assert openrtb_response.status_code == 200
    openrtb_payload = openrtb_response.json()
    assert openrtb_payload['id'] == 'req-1'
    assert openrtb_payload['seatbid'][0]['bid'][0]['impid'] == 'imp-1'


def test_capital_allocator_reports_reinvestment_and_allocations() -> None:
    module = _load_module('test_capital_allocator_advanced_main', 'services/capital-allocator/src/main.py')
    client = TestClient(module.app)

    response = client.post(
        '/allocate',
        json={
            'campaign_id': 'cmp-1',
            'score': 0.8,
            'spent': 50.0,
            'max_budget': 100.0,
            'daily_cap': 90.0,
            'min_step': 1.0,
            'max_step': 25.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload['reinvested_capital'] > 1000.0
    assert len(payload['allocations']) == 2
    assert round(sum(payload['allocations']), 4) == round(payload['reinvested_capital'], 4)
