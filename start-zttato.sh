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

sleep 6

################################
# Build services
################################

echo ""
echo "Building services..."
docker compose build

################################
# Start services
################################

echo ""
echo "Starting services..."
docker compose up -d

################################
# Run DB migrations
################################

echo ""
echo "Running database migrations..."

MIG="$ROOT/infrastructure/postgres/migrations/001_schema.sql"

if [ -f "$MIG" ]; then
  CONTAINER=$(docker ps -qf name=postgres | head -n1 || true)

  if [ -n "$CONTAINER" ]; then
    docker exec -i "$CONTAINER" psql -U postgres -f /dev/stdin < "$MIG" || true
  fi
fi

################################
# Start background workers
################################

echo ""
echo "Starting background workers..."

if [ -f "$ROOT/infrastructure/start/workers.sh" ]; then
  bash "$ROOT/infrastructure/start/workers.sh"
fi

################################
# Health checks
################################

echo ""
echo "Running health checks..."

sleep 5

curl -fs http://localhost:9100/docs || true
curl -fs http://localhost:9400/docs || true
curl -fs http://localhost:9500/arbitrage || true

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
