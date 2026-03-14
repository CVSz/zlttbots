# path: scripts/zttato-edge-doctor.sh
#!/usr/bin/env bash
#
# zTTato Edge Doctor
# Comprehensive diagnostics + optional auto-repair for Cloudflare Tunnel edge.
#
# Checks:
# - Env variables
# - Nameservers
# - DNS records
# - Cloudflare Tunnel status
# - TLS certificate coverage
# - Docker containers
# - Docker network connectivity
# - Service health
#
# Usage:
#   bash scripts/zttato-edge-doctor.sh
#   bash scripts/zttato-edge-doctor.sh --repair

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/cloudflare-devops/env"

REPAIR=false
if [[ "${1:-}" == "--repair" ]]; then
  REPAIR=true
fi

echo "======================================"
echo "zTTato Edge Doctor"
echo "Root: $ROOT"
echo "Repair mode: $REPAIR"
echo "======================================"

########################################
# Load ENV
########################################

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[ERROR] Missing env file: $ENV_FILE"
  exit 1
fi

set -o allexport
source "$ENV_FILE"
set +o allexport

: "${CF_API_TOKEN:?Missing CF_API_TOKEN}"
: "${CF_ZONE_ID:?Missing CF_ZONE_ID}"
: "${CF_ACCOUNT_ID:?Missing CF_ACCOUNT_ID}"
: "${CF_TUNNEL_ID:?Missing CF_TUNNEL_ID}"
: "${DOMAIN:?Missing DOMAIN}"
: "${SUBDOMAIN:?Missing SUBDOMAIN}"

########################################
# Dependencies
########################################

for bin in curl jq dig openssl docker; do
  if ! command -v "$bin" >/dev/null; then
    echo "[ERROR] Missing dependency: $bin"
    exit 1
  fi
done

########################################
# Helper
########################################

cf_api() {
  curl -s \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -H "Content-Type: application/json" \
    "$@"
}

########################################
# Nameserver Check
########################################

echo ""
echo "Nameserver Check"
echo "--------------------------------------"

NS=$(dig "$DOMAIN" NS +short)

echo "$NS"

if echo "$NS" | grep -qi "cloudflare"; then
  echo "[OK] Domain uses Cloudflare nameservers"
else
  echo "[WARN] Domain may not use Cloudflare nameservers"
fi

########################################
# DNS Check
########################################

echo ""
echo "DNS Records"
echo "--------------------------------------"

HOSTS=(
"$DOMAIN"
"$SUBDOMAIN.$DOMAIN"
"api.$DOMAIN"
"gpu.$DOMAIN"
"predict.$DOMAIN"
)

for h in "${HOSTS[@]}"; do
  echo "$h →"
  dig "$h" +short || true
done

########################################
# Tunnel Status
########################################

echo ""
echo "Cloudflare Tunnel"
echo "--------------------------------------"

docker ps --format '{{.Names}}' | grep -q cloudflared && \
docker logs zttato-cloudflared --tail 15 || \
echo "[WARN] cloudflared container not running"

########################################
# TLS Check
########################################

echo ""
echo "TLS Certificate Check"
echo "--------------------------------------"

for h in "${HOSTS[@]}"; do
  echo "Checking TLS: $h"
  CERT=$(echo | openssl s_client -connect "$h:443" -servername "$h" 2>/dev/null | grep "subject=" || true)

  if [[ -z "$CERT" ]]; then
    echo "[FAIL] TLS handshake failed"
  else
    echo "$CERT"
  fi
done

########################################
# HTTP Check
########################################

echo ""
echo "HTTP Endpoint Check"
echo "--------------------------------------"

for h in "${HOSTS[@]}"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$h" || true)
  echo "$h → HTTP $CODE"
done

########################################
# Docker Containers
########################################

echo ""
echo "Docker Containers"
echo "--------------------------------------"

docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

########################################
# Docker Network
########################################

echo ""
echo "Docker Network"
echo "--------------------------------------"

DOCKER_NETWORK="zttato-platform_zttato-net"
if ! docker network inspect "$DOCKER_NETWORK" >/dev/null 2>&1; then
  DOCKER_NETWORK="zttato-platform_default"
fi

if docker network inspect "$DOCKER_NETWORK" >/dev/null 2>&1; then
  echo "[OK] $DOCKER_NETWORK exists"
else
  echo "[WARN] docker network missing (checked zttato-platform_zttato-net and zttato-platform_default)"
fi

########################################
# Internal Connectivity
########################################

echo ""
echo "Internal Service Connectivity"
echo "--------------------------------------"

SERVICES=(
"market-crawler:9400"
"arbitrage-engine:9500"
"gpu-renderer:9300"
"viral-predictor:9100"
)

PROBE_CONTAINER="zttato-market-crawler"
if ! docker ps --format '{{.Names}}' | grep -qx "$PROBE_CONTAINER"; then
  PROBE_CONTAINER="zttato-arbitrage-engine"
fi

for s in "${SERVICES[@]}"; do
  host="${s%:*}"
  port="${s#*:}"
  if docker exec "$PROBE_CONTAINER" python -c "import socket; s=socket.create_connection(('$host',$port),3); s.close()" >/dev/null 2>&1; then
    echo "[OK] $s reachable"
  else
    echo "[FAIL] $s unreachable"
  fi
done

########################################
# Optional Auto Repair
########################################

if $REPAIR; then

  echo ""
  echo "Repair Mode"
  echo "--------------------------------------"

  echo "Re-applying tunnel ingress config"

  cf_api -X PUT \
  "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$CF_TUNNEL_ID/configurations" \
  --data "{
    \"config\": {
      \"ingress\": [
        {\"hostname\":\"$DOMAIN\",\"service\":\"http://market-crawler:9400\"},
        {\"hostname\":\"$SUBDOMAIN.$DOMAIN\",\"service\":\"http://market-crawler:9400\"},
        {\"hostname\":\"api.$DOMAIN\",\"service\":\"http://arbitrage-engine:9500\"},
        {\"hostname\":\"gpu.$DOMAIN\",\"service\":\"http://gpu-renderer:9300\"},
        {\"hostname\":\"predict.$DOMAIN\",\"service\":\"http://viral-predictor:9100\"},
        {\"service\":\"http_status:404\"}
      ]
    }
  }" >/dev/null

  echo "Restarting cloudflared container"
  docker restart zttato-cloudflared >/dev/null || true

  echo "Restarting docker stack"
  docker compose down >/dev/null
  docker compose up -d >/dev/null

  echo "Repair completed"
fi

########################################
# Finish
########################################

echo ""
echo "======================================"
echo "zTTato Edge Doctor Finished"
echo "======================================"

echo "Endpoints:"
echo "https://$DOMAIN"
echo "https://$SUBDOMAIN.$DOMAIN"
echo "https://api.$DOMAIN"
echo "https://gpu.$DOMAIN"
echo "https://predict.$DOMAIN"
