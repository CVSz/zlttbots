# path: scripts/repair-platform.sh
#!/usr/bin/env bash
#
# zTTato Platform Repair Tool
#
# Repairs common issues:
# - missing Dockerfiles for Python services
# - wrong docker-compose build contexts
# - missing .env variables
# - Cloudflare tunnel token export
# - rebuild docker stack
#
# Usage:
#   bash scripts/repair-platform.sh

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "======================================"
echo "zTTato Platform Repair Tool"
echo "Root: $ROOT"
echo "======================================"

########################################
# Services expected to be Python
########################################

PY_SERVICES=(
market-crawler
arbitrage-engine
gpu-renderer
viral-predictor
)

########################################
# 1. Repair Dockerfiles
########################################

echo ""
echo "Checking Dockerfiles..."

for SVC in "${PY_SERVICES[@]}"
do

DIR="$ROOT/services/$SVC"

if [ ! -d "$DIR" ]; then
    echo "Creating service directory: $SVC"
    mkdir -p "$DIR/src"
fi

if [ ! -f "$DIR/Dockerfile" ]; then

echo "Generating Dockerfile for $SVC"

cat > "$DIR/Dockerfile" <<EOF
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt || true

COPY src ./src

CMD ["python","src/main.py"]
EOF

fi

done

########################################
# 2. Fix docker-compose build paths
########################################

echo ""
echo "Fixing docker-compose build contexts..."

sed -i 's|services/market-crawler/docker|services/market-crawler|g' docker-compose.yml
sed -i 's|services/arbitrage-engine/docker|services/arbitrage-engine|g' docker-compose.yml
sed -i 's|services/gpu-renderer/docker|services/gpu-renderer|g' docker-compose.yml
sed -i 's|services/viral-predictor/docker|services/viral-predictor|g' docker-compose.yml

########################################
# 3. Remove obsolete version
########################################

echo ""
echo "Removing obsolete compose version..."

sed -i '/^version:/d' docker-compose.yml

########################################
# 4. Ensure .env exists
########################################

echo ""
echo "Checking environment file..."

if [ ! -f ".env" ]; then

cat > .env <<EOF
DB_URL=postgresql://postgres:postgres@postgres:5432/zttato
REDIS_URL=redis://redis:6379
EOF

echo ".env generated"

fi

########################################
# 5. Export Cloudflare tunnel token
########################################

if [ -f cloudflare-devops/env ]; then

echo ""
echo "Loading Cloudflare environment..."

export $(grep -v '^#' cloudflare-devops/env | xargs)

fi

########################################
# 6. Restart stack
########################################

echo ""
echo "Restarting Docker stack..."

docker compose down || true

docker compose \
-f docker-compose.yml \
-f cloudflare-devops/docker/docker-compose.cloudflare.yml \
up -d --build

########################################
# 7. Status
########################################

echo ""
echo "======================================"
echo "Repair completed"
echo "======================================"

echo ""
echo "Running containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Test endpoints:"
echo "https://zttato.zeaz.dev"
echo "https://admin.zttato.zeaz.dev"
echo "https://api.zttato.zeaz.dev"
