from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rebrand_zttato_to_zlttbots.py"
SPEC = importlib.util.spec_from_file_location("rebrand_script", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_audit_detects_legacy_tokens(tmp_path: Path) -> None:
    source = tmp_path / "service.py"
    source.write_text("name='zttato-platform'\n", encoding="utf-8")

    report = MODULE.audit_and_rebrand(tmp_path, apply=False)

    assert report["legacy_token_hit_count"] == 1
    assert report["affected_file_count"] == 1
    assert report["changed_file_count"] == 0
    assert report["affected_files"] == ["service.py"]


def test_apply_mode_rewrites_tokens(tmp_path: Path) -> None:
    source = tmp_path / "Dockerfile"
    source.write_text("ENV APP_NAME=zttato\n", encoding="utf-8")

    report = MODULE.audit_and_rebrand(tmp_path, apply=True)

    assert report["changed_file_count"] == 1
    assert source.read_text(encoding="utf-8") == "ENV APP_NAME=zlttbots\n"
