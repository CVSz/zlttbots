from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path


MODULE_PATH = Path("services/auto-ml/loop.py")
SPEC = importlib.util.spec_from_file_location("auto_ml_loop", MODULE_PATH)
assert SPEC and SPEC.loader
auto_ml_loop = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(auto_ml_loop)


def test_run_command_uses_argument_list_without_shell(monkeypatch) -> None:
    called: dict[str, object] = {}

    def fake_run(*args, **kwargs):
        called["args"] = args
        called["kwargs"] = kwargs
        return subprocess.CompletedProcess(args=["ok"], returncode=0, stdout="0.9", stderr="")

    monkeypatch.setattr(auto_ml_loop.subprocess, "run", fake_run)

    result = auto_ml_loop._run_command("echo", "ok")

    assert result is not None
    assert called["args"] == (("echo", "ok"),)
    assert "shell" not in called["kwargs"]


def test_evaluate_rejects_non_numeric_output(monkeypatch) -> None:
    monkeypatch.setattr(
        auto_ml_loop,
        "_run_command",
        lambda *_: subprocess.CompletedProcess(args=["eval"], returncode=0, stdout="not-a-number", stderr=""),
    )

    try:
        auto_ml_loop.evaluate()
    except RuntimeError as exc:
        assert "non-numeric" in str(exc)
    else:
        raise AssertionError("evaluate() should fail when eval.py is non-numeric")


def test_loop_returns_evaluate_failed_when_eval_command_fails(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(auto_ml_loop, "MODEL_DIR", tmp_path)
    monkeypatch.setattr(auto_ml_loop, "train", lambda: True)
    monkeypatch.setattr(auto_ml_loop, "evaluate", lambda: (_ for _ in ()).throw(RuntimeError("failed")))

    result = auto_ml_loop.loop()

    assert result["status"] == "evaluate_failed"
