# path: scripts/diagnose-zlttbots-edge.sh
#!/usr/bin/env bash
#
# zlttbots Edge Diagnostic Tool
#
# Checks:
# - environment configuration
# - Cloudflare DNS
# - Cloudflare Tunnel status
# - TLS handshake
# - Docker containers
# - internal service connectivity
#
# Usage:
#   bash scripts/diagnose-zlttbots-edge.sh

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ENV_FILE="cloudflare-devops/env"

echo "======================================"
echo "zlttbots Edge Diagnostic"
echo "Root: $ROOT"
echo "======================================"

########################################
# Load environment
########################################

if [ ! -f "$ENV_FILE" ]; then
  echo "[ERROR] Missing cloudflare-devops/env"
  exit 1
fi

export $(grep -v '^#' "$ENV_FILE" | xargs)

########################################
# Required tools
########################################

REQUIRED=(curl jq dig openssl docker)

for CMD in "${REQUIRED[@]}"; do
  if ! command -v "$CMD" >/dev/null 2>&1; then
    echo "[ERROR] Missing dependency: $CMD"
    exit 1
  fi
done

########################################
# Docker status
########################################

echo ""
echo "Docker Containers"
echo "--------------------------------------"

docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

########################################
# Cloudflare Tunnel status
########################################

echo ""
echo "Cloudflare Tunnel"
echo "--------------------------------------"

docker logs zlttbots-cloudflared --tail 20 || echo "cloudflared not running"

########################################
# DNS checks
########################################

echo ""
echo "DNS Resolution"
echo "--------------------------------------"

HOSTS=(
"$SUBDOMAIN.$DOMAIN"
"api.$SUBDOMAIN.$DOMAIN"
"gpu.$SUBDOMAIN.$DOMAIN"
"predict.$SUBDOMAIN.$DOMAIN"
)

for H in "${HOSTS[@]}"; do
  echo "$H →"
  dig "$H" +short || true
done

########################################
# TLS handshake
########################################

echo ""
echo "TLS Handshake"
echo "--------------------------------------"

for H in "${HOSTS[@]}"; do
  echo "Checking TLS: $H"
  echo | openssl s_client -connect "$H:443" -servername "$H" 2>/dev/null | grep "subject=" || echo "TLS FAILED"
done

########################################
# HTTP tests
########################################

echo ""
echo "HTTP Endpoint Tests"
echo "--------------------------------------"

for H in "${HOSTS[@]}"; do
  echo "curl https://$H"
  curl -s -o /dev/null -w "HTTP %{http_code}\n" "https://$H" || true
done

########################################
# Internal docker networking
########################################

echo ""
echo "Internal Service Connectivity"
echo "--------------------------------------"

TEST_CONTAINER="zlttbots-market-crawler-1"

SERVICES=(
"market-crawler:9400"
"arbitrage-engine:9500"
"gpu-renderer:9300"
"viral-predictor:9100"
)

for S in "${SERVICES[@]}"; do
  echo "Testing $S"
  docker exec "$TEST_CONTAINER" sh -c "wget -qO- http://$S" >/dev/null 2>&1 && echo "OK" || echo "FAILED"
done

########################################
# Cloudflare API check
########################################

echo ""
echo "Cloudflare Tunnel Configuration"
echo "--------------------------------------"

curl -s \
"https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$CF_TUNNEL_ID/configurations" \
-H "Authorization: Bearer $CF_API_TOKEN" | jq '.result.config.ingress'

########################################
# Summary
########################################

echo ""
echo "======================================"
echo "Diagnostic completed"
echo "======================================"

echo "Test URLs:"
echo "https://$SUBDOMAIN.$DOMAIN"
echo "https://api.$SUBDOMAIN.$DOMAIN"
echo "https://gpu.$SUBDOMAIN.$DOMAIN"
echo "https://predict.$SUBDOMAIN.$DOMAIN"
