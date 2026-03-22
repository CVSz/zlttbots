#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

log(){ printf '[upgrade] %s\n' "$*"; }
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

log "Running installer prerequisites"
bash "$ROOT_DIR/scripts/install-zttato-platform.sh"

log "Pulling published base images when available"
compose_cmd pull --ignore-pull-failures || true

log "Rebuilding local images"
compose_cmd build

log "Refreshing stack"
compose_cmd up -d --build --remove-orphans

if command -v npm >/dev/null 2>&1; then
  log "Refreshing Node dependencies"
  bash "$ROOT_DIR/scripts/install-node-services.sh"
fi

log "Upgrade completed"
