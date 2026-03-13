#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

run_worker() {
  local service_dir="$1"
  local worker_rel_path="$2"
  local label="$3"

  local python_bin="python3"
  if [ -x "$ROOT/$service_dir/.venv/bin/python" ]; then
    python_bin="$ROOT/$service_dir/.venv/bin/python"
  fi

  echo "Starting $label workers..."
  (
    cd "$ROOT/$service_dir"
    PYTHONPATH="$ROOT/$service_dir/src${PYTHONPATH:+:$PYTHONPATH}" "$python_bin" "$worker_rel_path"
  ) &
}

run_worker "services/market-crawler" "src/workers/worker.py" "crawler"
run_worker "services/arbitrage-engine" "src/workers/worker.py" "arbitrage"
run_worker "services/gpu-renderer" "src/worker/worker.py" "GPU renderer"
