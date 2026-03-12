#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$ROOT/pids"

SERVICES=(
viral-predictor
market-crawler
arbitrage-engine
gpu-renderer
crawler-worker
arbitrage-worker
gpu-worker
)

check_service(){

NAME="$1"
PID_FILE="$PID_DIR/$NAME.pid"

if [ ! -f "$PID_FILE" ]; then
return
fi

PID=$(cat "$PID_FILE")

if ! ps -p "$PID" >/dev/null 2>&1; then

echo "[supervisor] restarting $NAME"

bash "$ROOT/scripts/start-zttato.sh" >/dev/null 2>&1

fi

}

while true
do

for s in "${SERVICES[@]}"; do
check_service "$s"
done

sleep 10

done
