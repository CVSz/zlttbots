#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

log(){ printf '[start] %s\n' "$*"; }
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

ensure_env(){
  [[ -f .env ]] || bash "$ROOT_DIR/scripts/install-zttato-platform.sh"
}

smoke_check(){
  local url="$1"
  local name="$2"
  if curl -fsS "$url" >/dev/null 2>&1; then
    log "$name OK"
  else
    log "$name not ready yet"
  fi
}

ensure_env
log "Validating compose configuration"
compose_cmd config >/dev/null
log "Building and starting compose stack"
compose_cmd up -d --build --remove-orphans
log "Current compose status"
compose_cmd ps

sleep 3
smoke_check "http://localhost/" "gateway"
smoke_check "http://localhost:9100/docs" "viral-predictor"
smoke_check "http://localhost:9400/docs" "market-crawler"
smoke_check "http://localhost:9500/docs" "arbitrage-engine"
smoke_check "http://localhost:9300/docs" "gpu-renderer"

log "zTTato platform start completed"
