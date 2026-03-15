# path: start-zttato.sh
#!/usr/bin/env bash
#
# Unified launcher for zTTato Platform
# Combines:
# - permission fix
# - env loader
# - dependency install
# - docker infra startup
# - image build
# - service startup
# - workers
# - DB migration
# - health checks

set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$ROOT/logs"
PID_DIR="$ROOT/pids"

mkdir -p "$LOG_DIR" "$PID_DIR"

echo "================================="
echo "zTTato Platform Bootstrap"
echo "Root: $ROOT"
echo "================================="

################################
# Fix permissions
################################

echo "Fixing shell permissions..."
find "$ROOT" -type f -name "*.sh" -exec chmod +x {} \;

################################
# Load environment
################################

echo "Loading environment..."
if [ -f "$ROOT/infrastructure/start/env.sh" ]; then
  # shellcheck disable=SC1091
  source "$ROOT/infrastructure/start/env.sh"
fi

################################
# Install Node dependencies
################################

echo ""
echo "Installing Node dependencies..."

NODE_PKGS=$(find "$ROOT/services" -maxdepth 2 -name package.json)

for pkg in $NODE_PKGS
do
  dir=$(dirname "$pkg")
  echo "npm install -> $dir"
  (cd "$dir" && npm install --silent)
done

start_background_process() {
  local name="$1"
  local cmd="$2"
  local pid_file="$PID_DIR/$name.pid"
  local log_file="$LOG_DIR/$name.log"

  if [ -f "$pid_file" ]; then
    local existing_pid
    existing_pid=$(cat "$pid_file")

    if ps -p "$existing_pid" >/dev/null 2>&1; then
      echo "Process already running: $name (PID $existing_pid)"
      return
    fi
  fi

  nohup bash -c "$cmd" >"$log_file" 2>&1 &
  echo "$!" >"$pid_file"
  echo "Started: $name"
}

################################
# Start Node.js services
################################

echo ""
echo "Starting Node.js services..."

for pkg in $NODE_PKGS
do
  service_dir=$(dirname "$pkg")
  service_name=$(basename "$service_dir")

  if node -e "const p=require(process.argv[1]); process.exit((p.scripts&&p.scripts.start)?0:1)" "$pkg"; then
    start_background_process "node-$service_name" "cd '$service_dir' && npm start"
  fi
done

################################
# Install Python dependencies
################################

echo ""
echo "Installing Python dependencies..."

PY_PKGS=$(find "$ROOT/services" -maxdepth 2 -name requirements.txt)

for req in $PY_PKGS
do
  dir=$(dirname "$req")

  echo "Python env -> $dir"

  if [ ! -d "$dir/.venv" ]; then
    python3 -m venv "$dir/.venv"
  fi

  source "$dir/.venv/bin/activate"

  pip install --upgrade pip
  pip install -r "$req"

  deactivate
done

################################
# Start infrastructure
################################

echo ""
echo "Starting infrastructure..."
docker compose up -d postgres redis

# Ensure compose services get container-resolvable URLs without leaking
# container-only hostnames into locally executed workers.
COMPOSE_DB_URL="${CONTAINER_DB_URL:-postgresql://zttato:zttato@postgres:5432/zttato}"
COMPOSE_REDIS_URL="${CONTAINER_REDIS_URL:-redis://redis:6379}"

sleep 6

################################
# Build services
################################

echo ""
echo "Building services..."
DB_URL="$COMPOSE_DB_URL" REDIS_URL="$COMPOSE_REDIS_URL" docker compose build

################################
# Start services
################################

echo ""
echo "Starting services..."
DB_URL="$COMPOSE_DB_URL" REDIS_URL="$COMPOSE_REDIS_URL" docker compose up -d

################################
# Run DB migrations
################################

echo ""
echo "Running database migrations..."

MIG="$ROOT/infrastructure/postgres/migrations/001_schema.sql"

if [ -f "$MIG" ]; then
  CONTAINER=$(docker ps -qf name=postgres | head -n1 || true)

  if [ -n "$CONTAINER" ]; then
    docker exec -i "$CONTAINER" psql -U zttato -d zttato -f /dev/stdin < "$MIG" || true
  fi
fi

################################
# Start background workers
################################

echo ""
echo "Starting background workers..."

if [ "${START_LOCAL_WORKERS:-false}" = "true" ]; then
  if [ -f "$ROOT/infrastructure/start/workers.sh" ]; then
    bash "$ROOT/infrastructure/start/workers.sh"
  fi
else
  echo "Skipping local worker processes (containers already run worker services)."
  echo "Set START_LOCAL_WORKERS=true to run host-based workers."
fi

################################
# Health checks
################################

echo ""
echo "Running health checks..."

sleep 5

curl -fs http://localhost:9100/docs || true
curl -fs http://localhost:9400/docs || true
curl -fs http://localhost:9500/docs || true

################################
# Status
################################

echo ""
echo "================================="
echo "zTTato Platform Started"
echo "================================="

echo ""
echo "Active containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
