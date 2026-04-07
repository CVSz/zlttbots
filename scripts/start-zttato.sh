#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

LOG_DIR="$ROOT_DIR/logs"
PID_DIR="$ROOT_DIR/pids"

mkdir -p "$LOG_DIR" "$PID_DIR"

GREEN="\033[32m"
NC="\033[0m"

log(){ echo -e "${GREEN}[zTTato]${NC} $*"; }

############################################
# Locate docker compose
############################################

if docker compose version >/dev/null 2>&1; then
COMPOSE="docker compose"
else
COMPOSE="docker-compose"
fi

COMPOSE_FILE=""

if [ -f "$ROOT_DIR/docker-compose.yml" ]; then
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"

elif [ -f "$ROOT_DIR/infrastructure/docker/docker-compose.yml" ]; then
COMPOSE_FILE="$ROOT_DIR/infrastructure/docker/docker-compose.yml"

elif [ -f "$ROOT_DIR/docker/docker-compose.yml" ]; then
COMPOSE_FILE="$ROOT_DIR/docker/docker-compose.yml"

else
echo "ERROR: docker-compose.yml not found"
exit 1
fi

log "Using compose file: $COMPOSE_FILE"

############################################
# infrastructure
############################################

log "Starting infrastructure"

$COMPOSE -f "$COMPOSE_FILE" up -d postgres redis

############################################
# wait postgres
############################################

log "Waiting Postgres"

for i in {1..30}; do

if docker exec zlttbots-postgres-1 pg_isready -U zttato >/dev/null 2>&1; then
log "Postgres ready"
break
fi

sleep 1

done

############################################
# python env
############################################

if [ ! -d ".venv" ]; then
python3 -m venv .venv
fi

source .venv/bin/activate

############################################
# Node Services Dependency Install
############################################

log "Installing Node services"

NODE_SERVICES_DIR="$ROOT_DIR/services"

install_node_service(){

DIR="$1"

if [ ! -f "$DIR/package.json" ]; then
return
fi

log "npm ci -> $DIR"

(
cd "$DIR"

if [ -f package-lock.json ]; then
npm ci --silent
else
npm install --silent
fi

)

}

export -f install_node_service

find "$NODE_SERVICES_DIR" -maxdepth 1 -type d \
| tail -n +2 \
| xargs -I{} -P 4 bash -c 'install_node_service "$@"' _ {}


############################################
# run APIs
############################################

run(){

NAME="$1"
CMD="$2"

LOG="$LOG_DIR/$NAME.log"
PID="$PID_DIR/$NAME.pid"

if [ -f "$PID" ]; then
PIDVAL=$(cat "$PID")
if ps -p "$PIDVAL" >/dev/null; then
return
fi
fi

nohup bash -c "$CMD" > "$LOG" 2>&1 &

echo $! > "$PID"

}

run viral-predictor "cd services/viral-predictor && uvicorn src.main:app --host 0.0.0.0 --port 9100"
run market-crawler "cd services/market-crawler && uvicorn src.main:app --host 0.0.0.0 --port 9400"
run arbitrage-engine "cd services/arbitrage-engine && uvicorn src.main:app --host 0.0.0.0 --port 9500"
run gpu-renderer "cd services/gpu-renderer && uvicorn src.main:app --host 0.0.0.0 --port 9300"

############################################
# workers
############################################

run crawler-worker "python services/market-crawler/src/workers/worker.py"
run arbitrage-worker "python services/arbitrage-engine/src/workers/worker.py"
run gpu-worker "python services/gpu-renderer/src/worker/worker.py"

############################################
# tunnel
############################################

if [ -n "${CF_TUNNEL_TOKEN:-}" ]; then

if ! docker ps | grep -q cloudflared; then

docker run -d \
--name zttato-cloudflared \
--restart unless-stopped \
--network zlttbots_default \
cloudflare/cloudflared \
tunnel run --token "$CF_TUNNEL_TOKEN"

fi

fi

############################################
# health
############################################

sleep 4

curl -fs localhost:9100/docs >/dev/null && log "viral OK"
curl -fs localhost:9400/docs >/dev/null && log "crawler OK"
curl -fs localhost:9500/docs >/dev/null && log "arbitrage OK"
curl -fs localhost:9300/docs >/dev/null && log "renderer OK"

log "Platform started"
