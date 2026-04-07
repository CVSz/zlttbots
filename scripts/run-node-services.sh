#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ZLTTBOTS_ROOT="$ROOT"
# shellcheck disable=SC1091
source "$ROOT/scripts/node-services-lib.sh"

zlttbots_node_prepare_runtime_dirs

if ! command -v pm2 >/dev/null 2>&1; then
  echo 'ERROR: pm2 is required to start managed Node services.' >&2
  echo 'Install it with: npm install -g pm2' >&2
  exit 1
fi

printf '=================================\n'
printf 'Starting Node Services\n'
printf '=================================\n'

pm2 start "$ROOT/ecosystem.config.js" --update-env
pm2 save >/dev/null
pm2 ls

printf '✅ Node services started via PM2\n'
printf 'Logs: %s\n' "$ZLTTBOTS_NODE_LOG_DIR"
printf 'PIDs: %s\n' "$ZLTTBOTS_NODE_PID_DIR"
