import sys

import pytest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_module(module_name: str, relative_path: str):
    module_path = ROOT / relative_path
    spec = spec_from_file_location(module_name, module_path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_p2p_agent_rejects_wildcard_bind_by_default():
    module = _load_module("test_rl_p2p_agent", "services/rl-trainer/src/p2p_agent.py")
    with pytest.raises(ValueError, match="wildcard bind addresses are disabled by default"):
        module.P2PAgent(weights=[0.1, 0.2], host="0.0.0.0")


def test_p2p_agent_accepts_loopback_address():
    module = _load_module("test_rl_p2p_agent_loopback", "services/rl-trainer/src/p2p_agent.py")
    agent = module.P2PAgent(weights=[0.1, 0.2], host="127.0.0.1")
    assert agent.host == "127.0.0.1"


def test_resolve_bind_host_disables_wildcard_without_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("RTB_HOST", "0.0.0.0")
    monkeypatch.delenv("RTB_ALLOW_WILDCARD_BIND", raising=False)
    module = _load_module("test_rtb_bind_default", "services/rtb-engine/src/main.py")
    assert module.resolve_bind_host() == "127.0.0.1"


def test_resolve_bind_host_allows_wildcard_with_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("RTB_HOST", "::")
    monkeypatch.setenv("RTB_ALLOW_WILDCARD_BIND", "true")
    module = _load_module("test_rtb_bind_opt_in", "services/rtb-engine/src/main.py")
    assert module.resolve_bind_host() == "::"
