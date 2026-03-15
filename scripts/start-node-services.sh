#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/services"
LOG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/logs/node"

mkdir -p "$LOG_DIR"

SERVICES=(
  shopee-crawler
  tiktok-uploader
  tiktok-shop-miner
  tiktok-farm
  account-farm
  analytics
  admin-panel
  ai-video-generator
  click-tracker
)

echo "================================="
echo "Starting Node Services"
echo "Root: $ROOT"
echo "================================="

for SERVICE in "${SERVICES[@]}"; do
  SERVICE_DIR="$ROOT/$SERVICE"

  if [ ! -d "$SERVICE_DIR" ]; then
    echo "SKIP: $SERVICE_DIR not found"
    continue
  fi

  if [ ! -f "$SERVICE_DIR/package.json" ]; then
    echo "SKIP: $SERVICE_DIR missing package.json"
    continue
  fi

  echo "Installing dependencies -> $SERVICE"

  pushd "$SERVICE_DIR" >/dev/null

  if [ -f package-lock.json ]; then
    npm ci
  else
    npm install
  fi

  LOG_FILE="$LOG_DIR/$SERVICE.log"

  echo "Starting service -> $SERVICE"

  if npm run | grep -q "start"; then
    nohup npm run start >"$LOG_FILE" 2>&1 &
  elif npm run | grep -q "dev"; then
    nohup npm run dev >"$LOG_FILE" 2>&1 &
  else
    echo "WARN: $SERVICE has no start/dev script"
  fi

  popd >/dev/null
done

echo ""
echo "================================="
echo "Node Services Started"
echo "Logs: $LOG_DIR"
echo "================================="
