from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_payment_circuit_opens_after_repeated_failures():
    circuit = load_module('payment_circuit_test', 'services/payment/circuit.py')
    circuit.success()
    base = 100.0
    for offset in range(4):
        circuit.fail(now=base + offset)
    assert circuit.allow(now=base + 5) is False
    assert circuit.allow(now=base + 34) is True


def test_payment_audit_writes_json_line(tmp_path, monkeypatch):
    monkeypatch.setenv('PAYMENT_AUDIT_LOG', str(tmp_path / 'audit.log'))
    audit = load_module('payment_audit_test', 'services/payment/audit.py')
    audit.log('payment_success', {'id': 'abc'})
    payload = json.loads((tmp_path / 'audit.log').read_text().strip())
    assert payload['event'] == 'payment_success'
    assert payload['data'] == {'id': 'abc'}


def test_cost_control_enforces_daily_budget(monkeypatch):
    monkeypatch.setenv('MAX_DAILY_COST', '10')
    control = load_module('cost_control_test', 'services/cost/control.py')
    control.reset()
    assert control.allow(4) is True
    assert control.allow(6) is True
    assert control.allow(1) is False


def test_legal_gate_filters_jurisdictions():
    legal_gate = load_module('legal_gate_test', 'services/org/legal_gate.py')
    assert legal_gate.check('US') is True
    assert legal_gate.check('CN') is False


def test_treasury_caps_spending(monkeypatch):
    monkeypatch.setenv('DAILY_CAP', '100')
    treasury_mod = load_module('treasury_test', 'services/org/treasury.py')
    treasury = treasury_mod.Treasury()
    assert treasury.spend(60) is True
    assert treasury.spend(50) is False
