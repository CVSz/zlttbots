#!/usr/bin/env bash

set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PID_DIR="$ROOT/pids"

echo "Stopping processes"

for f in "$PID_DIR"/*.pid; do

[ -f "$f" ] || continue

PID=$(cat "$f")

kill "$PID" || true

rm -f "$f"

done

docker stop zlttbots-cloudflared >/dev/null 2>&1 || true

echo "Platform stopped"
