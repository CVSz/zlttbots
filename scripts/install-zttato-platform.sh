#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

log(){ printf '[install] %s\n' "$*"; }
fail(){ printf 'ERROR: %s\n' "$*" >&2; exit 1; }

require_cmd(){
  command -v "$1" >/dev/null 2>&1 || fail "$1 is required"
}

ensure_env(){
  if [[ -f .env ]]; then
    log ".env already exists"
    return
  fi

  if [[ -f configs/env/production.env ]]; then
    cp configs/env/production.env .env
    log "Created .env from configs/env/production.env"
    return
  fi

  cat > .env <<'ENVEOF'
DB_NAME=zttato
DB_USER=zttato
DB_PASSWORD=zttato
DB_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6379
FFMPEG_HWACCEL=none
FFMPEG_CPU_PRESET=veryfast
FFMPEG_CPU_CRF=23
PLATFORM_API_BASE=https://api.partner.example
PLATFORM_API_KEY=
AFFILIATE_WEBHOOK_SECRET=change-me
DEFAULT_DAILY_SPEND_LIMIT=100.0
HTTP_TIMEOUT=10
RATE_TOKENS=60
RATE_MAX_TOKENS=120
RATE_REFILL_PER_SEC=1
ENVEOF
  log "Created .env with local defaults"
}

install_node_dependencies(){
  if ! command -v npm >/dev/null 2>&1; then
    log "npm not found; skipping Node dependency installation"
    return
  fi

  log "Installing Node service dependencies"
  bash "$ROOT_DIR/scripts/install-node-services.sh"
}

validate_compose(){
  if docker compose version >/dev/null 2>&1; then
    docker compose config >/dev/null
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose config >/dev/null
  else
    fail "docker compose or docker-compose is required"
  fi
}

require_cmd docker
require_cmd python3
ensure_env
validate_compose
install_node_dependencies

log "zTTato platform install completed"
