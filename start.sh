#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo 'ERROR: docker is required to start the platform.' >&2
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo 'ERROR: docker compose or docker-compose is required.' >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  if [[ -f configs/env/production.env ]]; then
    cp configs/env/production.env .env
    echo 'Created .env from configs/env/production.env'
  else
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
ENVEOF
    echo 'Created .env with local defaults'
  fi
fi

echo 'Validating compose configuration...'
"${COMPOSE_CMD[@]}" config >/dev/null

echo 'Starting zTTato Platform (production profile)...'
"${COMPOSE_CMD[@]}" up -d --build --remove-orphans

echo 'Platform started.'
"${COMPOSE_CMD[@]}" ps
