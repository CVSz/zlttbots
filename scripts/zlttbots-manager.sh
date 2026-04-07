#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail(){ printf 'ERROR: %s\n' "$*" >&2; exit 1; }

compose_cmd(){
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    fail "docker compose or docker-compose is required"
  fi
}

status_cmd(){
  compose_cmd ps || true
  echo
  docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' || true
}

logs_cmd(){
  if [[ -n "${1:-}" ]]; then
    compose_cmd logs --tail=200 "$1"
  else
    compose_cmd logs --tail=200
  fi
}

usage(){
  cat <<'USAGE'
Usage: bash scripts/zlttbots-manager.sh <command> [args]

Commands:
  install         Prepare .env and install local dependencies
  start           Build and start the compose stack
  stop            Stop the compose stack
  restart         Restart the compose stack
  deploy          Run install + upgrade + start
  upgrade         Refresh images and restart the stack
  status          Show compose and docker status
  logs [service]  Show compose logs
  node            Show node-service usage helper
USAGE
}

case "${1:-}" in
  install)
    bash "$ROOT_DIR/scripts/install-zlttbots.sh"
    ;;
  start)
    bash "$ROOT_DIR/scripts/start-zlttbots.sh"
    ;;
  stop)
    compose_cmd down
    ;;
  restart)
    compose_cmd down
    bash "$ROOT_DIR/scripts/start-zlttbots.sh"
    ;;
  deploy)
    bash "$ROOT_DIR/scripts/deploy-zlttbots.sh"
    ;;
  upgrade)
    bash "$ROOT_DIR/scripts/upgrade-zlttbots.sh"
    ;;
  status)
    status_cmd
    ;;
  logs)
    logs_cmd "${2:-}"
    ;;
  node)
    echo 'Use: bash scripts/zlttbots-node.sh {install|start|stop|restart|status|logs [service]}'
    ;;
  *)
    usage
    ;;
esac
