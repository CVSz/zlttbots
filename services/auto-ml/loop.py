from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

MODEL_DIR = Path(os.getenv("MODEL_DIR", "/models"))
THRESHOLD = float(os.getenv("PROMOTE_DELTA", "0.02"))



def train() -> bool:
    return subprocess.call("python train.py", shell=True) == 0



def evaluate() -> float:
    output = subprocess.check_output("python eval.py", shell=True).decode().strip()
    return float(output)



def load_metric(path: Path) -> float:
    try:
        return float(path.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError):
        return 0.0



def save_metric(path: Path, value: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(value), encoding="utf-8")



def deploy() -> bool:
    return subprocess.call("bash deploy_model.sh", shell=True) == 0



def loop() -> dict[str, float | str]:
    previous_metric_path = MODEL_DIR / "metric.txt"
    previous = load_metric(previous_metric_path)
    if not train():
        return {"status": "train_failed"}

    score = evaluate()
    if score >= previous + THRESHOLD:
        if deploy():
            save_metric(previous_metric_path, score)
            return {"status": "promoted", "score": score}
        return {"status": "deploy_failed"}

    return {"status": "rejected", "score": score, "prev": previous}


if __name__ == "__main__":
    print(json.dumps(loop()))
