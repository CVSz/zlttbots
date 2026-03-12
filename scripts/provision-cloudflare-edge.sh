# path: scripts/provision-cloudflare-edge.sh
#!/usr/bin/env bash
#
# Cloudflare Edge Provisioner for zTTato Platform
#
# Responsibilities
# - validate env
# - ensure tunnel exists
# - ensure DNS records exist
# - push ingress config to Cloudflare
# - warm up TLS edge certificates
# - verify endpoints
#
# Usage:
#   bash scripts/provision-cloudflare-edge.sh

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/cloudflare-devops/env"

echo "======================================"
echo "zTTato Cloudflare Edge Provisioner"
echo "Root: $ROOT"
echo "======================================"

########################################
# Load ENV
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
: "${DOMAIN:?Missing DOMAIN}"
: "${SUBDOMAIN:?Missing SUBDOMAIN}"

########################################
# Dependencies
########################################

for bin in curl jq dig openssl; do
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

  local name="$1"

  echo "Checking DNS $name"

  record=$(cf_api \
    "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records?name=$name" \
    | jq -r '.result[0].id // empty')

  if [[ -z "$record" ]]; then

    echo "Creating DNS $name"

    cf_api -X POST \
      "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records" \
      --data "{
        \"type\":\"CNAME\",
        \"name\":\"$name\",
        \"content\":\"$CF_TUNNEL_ID.cfargotunnel.com\",
        \"proxied\":true,
        \"ttl\":1
      }" | jq

  else
    echo "DNS exists: $name"
  fi
}

########################################
# Ensure DNS records
########################################

ensure_dns "$SUBDOMAIN.$DOMAIN"
ensure_dns "api.$SUBDOMAIN.$DOMAIN"
ensure_dns "gpu.$SUBDOMAIN.$DOMAIN"
ensure_dns "predict.$SUBDOMAIN.$DOMAIN"

########################################
# Push ingress configuration
########################################

echo "Updating tunnel ingress config"

cf_api -X PUT \
"https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$CF_TUNNEL_ID/configurations" \
--data "{
  \"config\": {
    \"ingress\": [
      {
        \"hostname\":\"$SUBDOMAIN.$DOMAIN\",
        \"service\":\"http://market-crawler:9400\"
      },
      {
        \"hostname\":\"api.$SUBDOMAIN.$DOMAIN\",
        \"service\":\"http://arbitrage-engine:9500\"
      },
      {
        \"hostname\":\"gpu.$SUBDOMAIN.$DOMAIN\",
        \"service\":\"http://gpu-renderer:9300\"
      },
      {
        \"hostname\":\"predict.$SUBDOMAIN.$DOMAIN\",
        \"service\":\"http://viral-predictor:9100\"
      },
      {
        \"service\":\"http_status:404\"
      }
    ]
  }
}" | jq '.result.config.ingress'

########################################
# TLS warmup
########################################

echo "Warming Cloudflare TLS edge"

HOSTS=(
"$SUBDOMAIN.$DOMAIN"
"api.$SUBDOMAIN.$DOMAIN"
"gpu.$SUBDOMAIN.$DOMAIN"
"predict.$SUBDOMAIN.$DOMAIN"
)

for h in "${HOSTS[@]}"; do
  echo "Warmup $h"
  for i in {1..5}; do
    curl -s -k "https://$h" >/dev/null || true
  done
done

########################################
# Wait
########################################

echo "Waiting for certificate provisioning..."
sleep 30

########################################
# Verify TLS
########################################

echo ""
echo "TLS verification"

for h in "${HOSTS[@]}"; do
  echo "Checking $h"
  echo | openssl s_client -connect "$h:443" -servername "$h" 2>/dev/null | grep "subject=" || echo "TLS not ready"
done

########################################
# Verify HTTP
########################################

echo ""
echo "HTTP endpoint verification"

for h in "${HOSTS[@]}"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://$h" || true)
  echo "$h → HTTP $code"
done

########################################
# Finish
########################################

echo ""
echo "======================================"
echo "Cloudflare Edge Provision Complete"
echo "======================================"

echo "Endpoints:"
echo "https://$SUBDOMAIN.$DOMAIN"
echo "https://api.$SUBDOMAIN.$DOMAIN"
echo "https://gpu.$SUBDOMAIN.$DOMAIN"
echo "https://predict.$SUBDOMAIN.$DOMAIN"
