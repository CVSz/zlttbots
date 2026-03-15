#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$REPO_ROOT/logs/node/pids"

echo "Stopping Node services..."

if command -v pm2 >/dev/null 2>&1; then
  echo "Stopping PM2-managed processes..."
  pm2 delete all || true
  pm2 save || true
else
  echo "PM2 is not installed; checking nohup PID files."
fi

if [ -d "$PID_DIR" ]; then
  while IFS= read -r pid_file; do
    service_name="$(basename "$pid_file" .pid)"
    pid="$(cat "$pid_file")"

    if kill -0 "$pid" >/dev/null 2>&1; then
      echo "Stopping $service_name (PID $pid)"
      kill "$pid" || true
    else
      echo "$service_name is not running (stale PID $pid)"
    fi

    rm -f "$pid_file"
  done < <(find "$PID_DIR" -type f -name '*.pid' | sort)
fi

echo "Done."
