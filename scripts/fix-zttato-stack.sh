# path: scripts/fix-zttato-stack.sh
#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(pwd)"

echo "===================================="
echo "Fixing zTTato stack"
echo "===================================="

#####################################
# 1. export env
#####################################

if [ -f cloudflare-devops/env ]; then
    export $(grep -v '^#' cloudflare-devops/env | xargs)
fi

#####################################
# 2. fix docker compose paths
#####################################

echo "Fixing docker build contexts..."

sed -i 's|services/arbitrage-engine/docker|services/arbitrage-engine|g' docker-compose.yml
sed -i 's|services/market-crawler/docker|services/market-crawler|g' docker-compose.yml
sed -i 's|services/gpu-renderer/docker|services/gpu-renderer|g' docker-compose.yml
sed -i 's|services/viral-predictor/docker|services/viral-predictor|g' docker-compose.yml

#####################################
# 3. remove obsolete version
#####################################

sed -i '/^version:/d' docker-compose.yml

#####################################
# 4. create .env if missing
#####################################

if [ ! -f .env ]; then

cat > .env <<EOF
DB_URL=postgresql://postgres:postgres@postgres:5432/zttato
REDIS_URL=redis://redis:6379
EOF

fi

#####################################
# 5. export tunnel token
#####################################

if grep -q CF_TUNNEL_TOKEN cloudflare-devops/env; then
    export CF_TUNNEL_TOKEN=$(grep CF_TUNNEL_TOKEN cloudflare-devops/env | cut -d= -f2)
fi

#####################################
# 6. restart stack
#####################################

docker compose down || true

docker compose \
-f docker-compose.yml \
-f cloudflare-devops/docker/docker-compose.cloudflare.yml \
up -d --build

echo ""
echo "===================================="
echo "Stack repaired and restarted"
echo "===================================="
