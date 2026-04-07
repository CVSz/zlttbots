# path: scripts/deploy-cloudflare-edge.sh
#!/usr/bin/env bash
#
# Deploy Cloudflare Tunnel + DNS + Ingress for zlttbots
#
# Requirements:
# - env file with CF_API_TOKEN CF_ACCOUNT_ID CF_ZONE_ID DOMAIN SUBDOMAIN
# - docker + docker compose installed
# - jq installed
#
# Usage:
#   bash scripts/deploy-cloudflare-edge.sh

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ENV_FILE="cloudflare-devops/env"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing cloudflare-devops/env"
  exit 1
fi

export $(grep -v '^#' "$ENV_FILE" | xargs)

echo "======================================"
echo "Cloudflare Edge Deployment"
echo "======================================"

########################################
# dependency check
########################################

command -v curl >/dev/null || { echo "curl required"; exit 1; }
command -v jq >/dev/null || { echo "jq required"; exit 1; }
command -v docker >/dev/null || { echo "docker required"; exit 1; }

########################################
# check existing tunnel
########################################

echo "Checking existing tunnel..."

TUNNEL_JSON=$(curl -s \
https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel \
-H "Authorization: Bearer $CF_API_TOKEN")

TUNNEL_ID=$(echo "$TUNNEL_JSON" | jq -r ".result[] | select(.name==\"$SUBDOMAIN\") | .id")

########################################
# create tunnel if missing
########################################

if [ -z "$TUNNEL_ID" ] || [ "$TUNNEL_ID" == "null" ]; then

  echo "Creating tunnel..."

  SECRET=$(openssl rand -base64 32)

  CREATE=$(curl -s -X POST \
  https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data "{\"name\":\"$SUBDOMAIN\",\"tunnel_secret\":\"$SECRET\"}")

  SUCCESS=$(echo "$CREATE" | jq -r '.success')

  if [ "$SUCCESS" != "true" ]; then
    echo "Tunnel creation failed:"
    echo "$CREATE"
    exit 1
  fi

  TUNNEL_ID=$(echo "$CREATE" | jq -r '.result.id')

fi

echo "Tunnel ID: $TUNNEL_ID"

########################################
# get token
########################################

echo "Fetching tunnel token..."

TOKEN=$(curl -s \
https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID/token \
-H "Authorization: Bearer $CF_API_TOKEN" | jq -r '.result')

########################################
# save token
########################################

grep -v CF_TUNNEL_TOKEN "$ENV_FILE" > "$ENV_FILE.tmp" || true
mv "$ENV_FILE.tmp" "$ENV_FILE"

echo "CF_TUNNEL_TOKEN=$TOKEN" >> "$ENV_FILE"

export CF_TUNNEL_TOKEN="$TOKEN"

########################################
# configure ingress
########################################

echo "Configuring tunnel ingress..."

curl -s -X PUT \
https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID/configurations \
-H "Authorization: Bearer $CF_API_TOKEN" \
-H "Content-Type: application/json" \
--data '{
"config":{
"ingress":[
{
"hostname":"'"$SUBDOMAIN.$DOMAIN"'",
"service":"http://market-crawler:9400"
},
{
"hostname":"api.'"$SUBDOMAIN.$DOMAIN"'",
"service":"http://arbitrage-engine:9500"
},
{
"hostname":"gpu.'"$SUBDOMAIN.$DOMAIN"'",
"service":"http://gpu-renderer:9300"
},
{
"hostname":"predict.'"$SUBDOMAIN.$DOMAIN"'",
"service":"http://viral-predictor:9100"
},
{
"service":"http_status:404"
}
]
}
}'

########################################
# DNS record
########################################

echo "Ensuring DNS record..."

DNS=$(curl -s \
"https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records?name=$SUBDOMAIN.$DOMAIN" \
-H "Authorization: Bearer $CF_API_TOKEN")

RECORD_ID=$(echo "$DNS" | jq -r '.result[0].id')

if [ "$RECORD_ID" != "null" ]; then

  curl -s -X DELETE \
  "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records/$RECORD_ID" \
  -H "Authorization: Bearer $CF_API_TOKEN"

fi

curl -s -X POST \
"https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records" \
-H "Authorization: Bearer $CF_API_TOKEN" \
-H "Content-Type: application/json" \
--data '{
"type":"CNAME",
"name":"'"$SUBDOMAIN"'",
"content":"'"$TUNNEL_ID"'.cfargotunnel.com",
"ttl":1,
"proxied":true
}'

########################################
# start tunnel container
########################################

echo "Starting cloudflared..."

docker compose \
-f docker-compose.yml \
-f cloudflare-devops/docker/docker-compose.cloudflare.yml \
up -d cloudflared

########################################
# verification
########################################

echo ""
echo "======================================"
echo "Cloudflare Edge Deployed"
echo "======================================"

echo "Tunnel ID: $TUNNEL_ID"

echo ""
echo "Routes:"
echo "https://$SUBDOMAIN.$DOMAIN"
echo "https://api.$SUBDOMAIN.$DOMAIN"
echo "https://gpu.$SUBDOMAIN.$DOMAIN"
echo "https://predict.$SUBDOMAIN.$DOMAIN"

echo ""
echo "Tunnel status:"
docker logs zlttbots-cloudflared --tail 10
