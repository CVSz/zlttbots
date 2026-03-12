# scripts/deploy-zttato-production.sh
#!/usr/bin/env bash

set -Eeuo pipefail

# ==========================================
# zTTato Production Deployment
# ==========================================
# Responsibilities
# - Validate environment
# - Fix kernel networking for Cloudflare QUIC
# - Build / restart docker stack
# - Ensure cloudflared network connectivity
# - Verify internal services
# - Warm Cloudflare edge
# - Validate endpoints
# ==========================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "======================================"
echo "zTTato Production Deployment"
echo "Root: $ROOT_DIR"
echo "======================================"

# ------------------------------------------------
# Load environment
# ------------------------------------------------

if [[ -f "$ROOT_DIR/env" ]]; then
    set -a
    source "$ROOT_DIR/env"
    set +a
fi

if [[ -z "${CF_API_TOKEN:-}" || -z "${CF_ACCOUNT_ID:-}" || -z "${CF_ZONE_ID:-}" ]]; then
    echo "ERROR: Missing Cloudflare environment variables"
    exit 1
fi

# ------------------------------------------------
# Kernel tuning for QUIC / Cloudflare Tunnel
# ------------------------------------------------

echo
echo "Configuring kernel buffers"

sysctl -w net.core.rmem_max=7500000 >/dev/null
sysctl -w net.core.wmem_max=7500000 >/dev/null
sysctl -w net.core.netdev_max_backlog=4096 >/dev/null

if ! grep -q "net.core.rmem_max=7500000" /etc/sysctl.conf; then
    echo "net.core.rmem_max=7500000" >> /etc/sysctl.conf
fi

if ! grep -q "net.core.wmem_max=7500000" /etc/sysctl.conf; then
    echo "net.core.wmem_max=7500000" >> /etc/sysctl.conf
fi

# ------------------------------------------------
# Docker stack deploy
# ------------------------------------------------

echo
echo "Deploying docker stack"

docker compose down --remove-orphans || true

docker compose build --parallel

docker compose up -d

sleep 5

# ------------------------------------------------
# Ensure docker network exists
# ------------------------------------------------

echo
echo "Checking docker network"

NETWORK="zttato-platform_default"

if ! docker network inspect "$NETWORK" >/dev/null 2>&1; then
    echo "Creating docker network"
    docker network create "$NETWORK"
fi

# ------------------------------------------------
# Ensure cloudflared connected to network
# ------------------------------------------------

echo
echo "Ensuring cloudflared network connectivity"

if docker ps --format '{{.Names}}' | grep -q "zttato-cloudflared"; then

    if ! docker network inspect "$NETWORK" | grep -q zttato-cloudflared; then
        docker network connect "$NETWORK" zttato-cloudflared || true
    fi

else
    echo "Starting cloudflared"

    docker run -d \
        --name zttato-cloudflared \
        --network "$NETWORK" \
        --restart unless-stopped \
        cloudflare/cloudflared:latest \
        tunnel --no-autoupdate run --token "$CF_TUNNEL_TOKEN"
fi

# ------------------------------------------------
# Internal service validation
# ------------------------------------------------

echo
echo "Checking internal services"

check_service() {

    local name=$1
    local port=$2

    if curl -s "http://localhost:${port}/docs" >/dev/null; then
        echo "[OK] $name"
    else
        echo "[WARN] $name not responding"
    fi
}

check_service "arbitrage-engine" 9500
check_service "gpu-renderer" 9300
check_service "viral-predictor" 9100
check_service "market-crawler" 9400

# ------------------------------------------------
# Warm Cloudflare edge
# ------------------------------------------------

echo
echo "Warming Cloudflare edge"

domains=(
"zeaz.dev"
"zttato.zeaz.dev"
"api.zeaz.dev"
"gpu.zeaz.dev"
"predict.zeaz.dev"
)

for d in "${domains[@]}"; do
    curl -ks "https://${d}" >/dev/null || true
done

# ------------------------------------------------
# TLS verification
# ------------------------------------------------

echo
echo "TLS verification"

for d in "${domains[@]}"; do

    if echo | openssl s_client -connect "${d}:443" -servername "$d" 2>/dev/null | grep -q "subject="; then
        echo "[OK] TLS $d"
    else
        echo "[WARN] TLS not ready $d"
    fi

done

# ------------------------------------------------
# Endpoint verification
# ------------------------------------------------

echo
echo "HTTP endpoint verification"

for d in "${domains[@]}"; do

    code=$(curl -ks -o /dev/null -w "%{http_code}" "https://${d}")

    echo "$d → HTTP $code"

done

# ------------------------------------------------
# Show running containers
# ------------------------------------------------

echo
echo "Running containers"

docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# ------------------------------------------------
# Final status
# ------------------------------------------------

echo
echo "======================================"
echo "zTTato Production Deployment Complete"
echo "======================================"
echo
echo "Endpoints:"
echo "https://zeaz.dev"
echo "https://zttato.zeaz.dev"
echo "https://api.zeaz.dev"
echo "https://gpu.zeaz.dev"
echo "https://predict.zeaz.dev"
echo
echo "Swagger:"
echo "https://api.zeaz.dev/docs"
echo "https://gpu.zeaz.dev/docs"
echo "https://predict.zeaz.dev/docs"
echo "https://zttato.zeaz.dev/docs"
echo
echo "Diagnostics:"
echo "bash scripts/zttato-edge-doctor.sh"
echo
