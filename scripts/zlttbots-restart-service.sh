#!/usr/bin/env bash

SERVICE="$1"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PORT=""

case "$SERVICE" in

viral)
PORT=9100
DIR=services/viral-predictor
;;

crawler)
PORT=9400
DIR=services/market-crawler
;;

arbitrage)
PORT=9500
DIR=services/arbitrage-engine
;;

gpu)
PORT=9300
DIR=services/gpu-renderer
;;

esac

echo "Starting new instance"

cd "$ROOT/$DIR"

uvicorn src.main:app --port $PORT --host 0.0.0.0 &
NEWPID=$!

sleep 3

kill $(lsof -t -i:$PORT) || true

echo "Restart complete"
