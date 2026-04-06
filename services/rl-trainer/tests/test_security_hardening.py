from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from agent_replicator import build_remote_command, parse_targets
from autonomy.redteam import plan, sample_payload


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
    assert first == second


def test_plan_uses_deterministic_payloads() -> None:
    first = plan("sandbox")
    second = plan("sandbox")
    assert first == second
