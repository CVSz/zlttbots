#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ZLTTBOTS_ROOT="$ROOT"
# shellcheck disable=SC1091
source "$ROOT/scripts/node-services-lib.sh"

zlttbots_node_prepare_runtime_dirs

printf '=================================\n'
printf 'Stopping Node Services\n'
printf '=================================\n'

if command -v pm2 >/dev/null 2>&1; then
  for service in "${ZLTTBOTS_NODE_SERVICES[@]}"; do
    app_name="node-$service"
    if pm2 describe "$app_name" >/dev/null 2>&1; then
      printf '[STOP] %s\n' "$app_name"
      pm2 delete "$app_name" >/dev/null
    else
      printf '[SKIP] %s (not running in PM2)\n' "$app_name"
    fi
  done
  pm2 save >/dev/null || true
else
  printf '[WARN] pm2 not found; removing stale pid files only\n'
fi

find "$ZLTTBOTS_NODE_PID_DIR" -maxdepth 1 -type f -name '*.pid' -delete
printf '✅ Node services stopped\n'
