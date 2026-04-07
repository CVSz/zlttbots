from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.append(str(SRC_DIR))

from agent_replicator import build_remote_command, parse_targets
from autonomy.redteam import plan, sample_payload


def _parse_module(relative_path: str) -> ast.AST:
    file_path = SRC_DIR / relative_path
    return ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))


def _iter_calls(tree: ast.AST) -> list[ast.Call]:
    return [node for node in ast.walk(tree) if isinstance(node, ast.Call)]


def test_parse_targets_rejects_invalid_host() -> None:
    with pytest.raises(ValueError):
        parse_targets("root@bad host:k8s")


def test_build_remote_command_rejects_invalid_image() -> None:
    with pytest.raises(ValueError):
        build_remote_command("docker-compose", "bad image")


def test_sample_payload_is_deterministic() -> None:
    seed = "sandbox:model-service:http://model-service:8000/predict"
    first = sample_payload(seed)
    second = sample_payload(seed)
    if first != second:
        raise AssertionError("sample_payload must be deterministic for identical seeds")


def test_plan_uses_deterministic_payloads() -> None:
    first = plan("sandbox")
    second = plan("sandbox")
    if first != second:
        raise AssertionError("plan output must be deterministic for identical inputs")


def test_agent_replicator_does_not_use_subprocess_run() -> None:
    tree = _parse_module("agent_replicator.py")
    for call in _iter_calls(tree):
        if not isinstance(call.func, ast.Attribute):
            continue
        if call.func.attr != "run":
            continue
        if isinstance(call.func.value, ast.Name) and call.func.value.id == "subprocess":
            raise AssertionError("subprocess.run is prohibited in agent_replicator.py")


def test_redteam_does_not_use_non_deterministic_random_calls() -> None:
    tree = _parse_module("autonomy/redteam.py")
    for call in _iter_calls(tree):
        if not isinstance(call.func, ast.Attribute):
            continue
        if call.func.attr != "randint":
            continue
        if isinstance(call.func.value, ast.Name) and call.func.value.id == "random":
            raise AssertionError("random.randint is prohibited in autonomy/redteam.py")
