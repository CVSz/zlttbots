#!/usr/bin/env bash

echo "Starting crawler workers..."
python services/market-crawler/src/workers/worker.py &

echo "Starting arbitrage workers..."
python services/arbitrage-engine/src/workers/worker.py &

echo "Starting GPU renderer workers..."
python services/gpu-renderer/src/worker/worker.py &
