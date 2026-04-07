# path: scripts/migrate-edge-domain.sh
#!/usr/bin/env bash
#
# zlttbots Edge Domain Migration + Full Fix
#
# Migrates Cloudflare Tunnel routes to:
#   zeaz.dev
#   api.zeaz.dev
#   gpu.zeaz.dev
#   predict.zeaz.dev
#   zlttbots.zeaz.dev
#
# Performs:
# - DNS record reconciliation
# - Tunnel ingress update
# - Cloudflared restart
# - Docker network attach
# - TLS warm-up
# - Endpoint verification
#
# Usage:
#   bash scripts/migrate-edge-domain.sh
#

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/cloudflare-devops/env"

echo "======================================"
echo "zlttbots Edge Domain Migration"
echo "Root: $ROOT"
echo "======================================"

########################################
# Load environment
########################################

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE"
  exit 1
fi

set -o allexport
source "$ENV_FILE"
set +o allexport

: "${CF_API_TOKEN:?Missing CF_API_TOKEN}"
: "${CF_ZONE_ID:?Missing CF_ZONE_ID}"
: "${CF_ACCOUNT_ID:?Missing CF_ACCOUNT_ID}"
: "${CF_TUNNEL_ID:?Missing CF_TUNNEL_ID}"

DOMAIN="zeaz.dev"

########################################
# Dependencies
########################################

for bin in curl jq dig docker openssl; do
  if ! command -v "$bin" >/dev/null; then
    echo "Missing dependency: $bin"
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
# DNS ensure
########################################

ensure_dns() {

  NAME=$1

  echo "Checking DNS: $NAME"

  EXIST=$(cf_api \
  "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records?name=$NAME" \
  | jq -r '.result[0].id // empty')

  if [[ -z "$EXIST" ]]; then

    echo "Creating DNS: $NAME"

    cf_api -X POST \
    "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records" \
    --data "{
      \"type\":\"CNAME\",
      \"name\":\"$NAME\",
      \"content\":\"$CF_TUNNEL_ID.cfargotunnel.com\",
      \"proxied\":true,
      \"ttl\":1
    }" | jq '.success'

  else
    echo "DNS exists: $NAME"
  fi
}

########################################
# Ensure DNS
########################################

ensure_dns "zlttbots.$DOMAIN"
ensure_dns "api.$DOMAIN"
ensure_dns "gpu.$DOMAIN"
ensure_dns "predict.$DOMAIN"

########################################
# Update tunnel ingress
########################################

echo "Updating Cloudflare Tunnel ingress"

cf_api -X PUT \
"https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$CF_TUNNEL_ID/configurations" \
--data "{
  \"config\": {
    \"ingress\": [
      {
        \"hostname\":\"zlttbots.$DOMAIN\",
        \"service\":\"http://market-crawler:9400\"
      },
      {
        \"hostname\":\"api.$DOMAIN\",
        \"service\":\"http://arbitrage-engine:9500\"
      },
      {
        \"hostname\":\"gpu.$DOMAIN\",
        \"service\":\"http://gpu-renderer:9300\"
      },
      {
        \"hostname\":\"predict.$DOMAIN\",
        \"service\":\"http://viral-predictor:9100\"
      },
      {
        \"service\":\"http_status:404\"
      }
    ]
  }
}" | jq '.result.config.ingress'

########################################
# Ensure docker network connectivity
########################################

echo "Checking docker network"

NETWORK="zlttbots_default"

if docker network inspect "$NETWORK" >/dev/null 2>&1; then
  echo "Network exists: $NETWORK"
else
  echo "Creating network: $NETWORK"
  docker network create "$NETWORK"
fi

echo "Ensuring cloudflared attached to network"

if ! docker inspect zlttbots-cloudflared \
| jq -e ".[0].NetworkSettings.Networks.\"$NETWORK\"" >/dev/null 2>&1; then

  docker network connect "$NETWORK" zlttbots-cloudflared || true
fi

########################################
# Restart tunnel
########################################

echo "Restarting cloudflared"

docker restart zlttbots-cloudflared >/dev/null

########################################
# TLS warmup
########################################

echo "Warming TLS edge"

HOSTS=(
"zlttbots.$DOMAIN"
"api.$DOMAIN"
"gpu.$DOMAIN"
"predict.$DOMAIN"
)

for h in "${HOSTS[@]}"; do
  echo "Warmup $h"
  for i in {1..5}; do
    curl -s -k "https://$h" >/dev/null || true
  done
done

echo "Waiting for certificate provisioning"
sleep 30

########################################
# Verify TLS
########################################

echo ""
echo "TLS verification"

for h in "${HOSTS[@]}"; do

  echo "Checking $h"

  CERT=$(echo | openssl s_client -connect "$h:443" -servername "$h" 2>/dev/null | grep subject= || true)

  if [[ -z "$CERT" ]]; then
    echo "TLS NOT READY"
  else
    echo "$CERT"
  fi

done

########################################
# Verify HTTP
########################################

echo ""
echo "Endpoint verification"

for h in "${HOSTS[@]}"; do

  CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$h" || true)

  echo "$h → HTTP $CODE"

done

########################################
# Final status
########################################

echo ""
echo "======================================"
echo "Edge Migration Complete"
echo "======================================"

echo "Endpoints:"
echo "https://zlttbots.$DOMAIN"
echo "https://api.$DOMAIN"
echo "https://gpu.$DOMAIN"
echo "https://predict.$DOMAIN"
