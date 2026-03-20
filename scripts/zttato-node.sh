#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ZTTATO_ROOT="$ROOT"
# shellcheck disable=SC1091
source "$ROOT/scripts/node-services-lib.sh"

usage() {
  echo 'Usage: scripts/zttato-node.sh {install|start|stop|restart|status|logs [service]}'
}

case "${1:-}" in
  install)
    bash "$ROOT/scripts/install-node-services.sh"
    ;;
  start)
    bash "$ROOT/scripts/run-node-services.sh"
    ;;
  stop)
    bash "$ROOT/scripts/stop-node-services.sh"
    ;;
  restart)
    bash "$ROOT/scripts/stop-node-services.sh"
    bash "$ROOT/scripts/run-node-services.sh"
    ;;
  status)
    if ! command -v pm2 >/dev/null 2>&1; then
      echo 'PM2 is not installed.' >&2
      exit 1
    fi
    pm2 ls
    ;;
  logs)
    if ! command -v pm2 >/dev/null 2>&1; then
      echo 'PM2 is not installed.' >&2
      exit 1
    fi

    if [[ -n "${2:-}" ]]; then
      pm2 logs "node-$2"
    else
      echo "Managed log files: $ZTTATO_NODE_LOG_DIR"
      find "$ZTTATO_NODE_LOG_DIR" -maxdepth 1 -type f | sort
    fi
    ;;
  *)
    usage
    exit 1
    ;;
esac
