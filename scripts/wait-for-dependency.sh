#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <host> <port> [timeout_seconds]" >&2
  exit 64
fi

host="$1"
port="$2"
timeout_seconds="${3:-120}"
start_ts="$(date +%s)"

while true; do
  if python - "$host" "$port" <<'PY'
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])
with socket.create_connection((host, port), timeout=2):
    pass
PY
  then
    echo "Dependency ready: ${host}:${port}"
    exit 0
  fi

  now="$(date +%s)"
  elapsed=$((now - start_ts))
  if (( elapsed >= timeout_seconds )); then
    echo "Timed out waiting for ${host}:${port} after ${timeout_seconds}s" >&2
    exit 70
  fi

  echo "Waiting for ${host}:${port}... (${elapsed}s elapsed)"
  sleep 2
done
