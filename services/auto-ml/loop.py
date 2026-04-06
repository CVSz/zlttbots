from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

MODEL_DIR = Path(os.getenv("MODEL_DIR", "/models"))
THRESHOLD = float(os.getenv("PROMOTE_DELTA", "0.02"))
COMMAND_TIMEOUT_SECONDS = int(os.getenv("AUTO_ML_COMMAND_TIMEOUT_SECONDS", "900"))
SCRIPT_DIR = Path(__file__).resolve().parent

logger = logging.getLogger("auto_ml.loop")


def _log(event: str, **fields: Any) -> None:
    payload: dict[str, Any] = {"event": event, **fields}
    logger.info(json.dumps(payload, sort_keys=True))


def _run_command(*args: str) -> subprocess.CompletedProcess[str] | None:
    try:
        completed = subprocess.run(
            args,
            cwd=SCRIPT_DIR,
            check=False,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        _log("command_spawn_failed", command=list(args))
        return None

    _log(
        "command_executed",
        command=list(args),
        returncode=completed.returncode,
        stderr=completed.stderr.strip(),
    )
    return completed



def train() -> bool:
    completed = _run_command(sys.executable, "train.py")
    return bool(completed) and completed.returncode == 0



def evaluate() -> float:
    completed = _run_command(sys.executable, "eval.py")
    if not completed or completed.returncode != 0:
        raise RuntimeError("evaluate command failed")

    try:
        return float(completed.stdout.strip())
    except ValueError as exc:
        raise RuntimeError("evaluate command returned non-numeric score") from exc



def load_metric(path: Path) -> float:
    try:
        return float(path.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError):
        return 0.0



def save_metric(path: Path, value: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(value), encoding="utf-8")



def deploy() -> bool:
    completed = _run_command("bash", "deploy_model.sh")
    return bool(completed) and completed.returncode == 0



def loop() -> dict[str, float | str]:
    previous_metric_path = MODEL_DIR / "metric.txt"
    previous = load_metric(previous_metric_path)
    if not train():
        _log("loop_exit", status="train_failed")
        return {"status": "train_failed"}

    try:
        score = evaluate()
    except RuntimeError:
        _log("loop_exit", status="evaluate_failed")
        return {"status": "evaluate_failed"}

    if score >= previous + THRESHOLD:
        if deploy():
            save_metric(previous_metric_path, score)
            _log("loop_exit", status="promoted", score=score, prev=previous)
            return {"status": "promoted", "score": score}
        _log("loop_exit", status="deploy_failed", score=score, prev=previous)
        return {"status": "deploy_failed"}

    _log("loop_exit", status="rejected", score=score, prev=previous)
    return {"status": "rejected", "score": score, "prev": previous}


if __name__ == "__main__":
    print(json.dumps(loop()))
