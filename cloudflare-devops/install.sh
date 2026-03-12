#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

source "$ROOT/env"

echo "================================"
echo "Cloudflare Edge Installer"
echo "================================"

########################################
# dependencies
########################################

if ! command -v jq >/dev/null 2>&1; then
    sudo apt update
    sudo apt install jq -y
fi

if ! command -v cloudflared >/dev/null 2>&1; then

echo "Installing cloudflared..."

curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
-o /usr/local/bin/cloudflared

chmod +x /usr/local/bin/cloudflared

fi

########################################
# create tunnel
########################################

echo "Creating tunnel..."

RESPONSE=$(bash api/create-tunnel.sh)

SUCCESS=$(echo "$RESPONSE" | jq -r '.success')

if [[ "$SUCCESS" != "true" ]]; then
    echo "$RESPONSE"
    echo "Tunnel creation failed"
    exit 1
fi

TUNNEL_ID=$(echo "$RESPONSE" | jq -r '.result.id')
TOKEN=$(echo "$RESPONSE" | jq -r '.result.token')

echo "Tunnel ID: $TUNNEL_ID"

########################################
# save token
########################################

grep -v CF_TUNNEL_TOKEN "$ROOT/env" > "$ROOT/env.tmp" || true
mv "$ROOT/env.tmp" "$ROOT/env"

echo "CF_TUNNEL_TOKEN=$TOKEN" >> "$ROOT/env"

########################################
# create dns
########################################

echo "Creating DNS..."

bash api/create-dns.sh "$TUNNEL_ID"

########################################
# export env
########################################

export $(grep -v '^#' "$ROOT/env" | xargs)

########################################
# start docker tunnel
########################################

docker compose \
-f ../docker-compose.yml \
-f docker/docker-compose.cloudflare.yml \
up -d

echo ""
echo "================================"
echo "Cloudflare Tunnel Running"
echo "================================"

echo "https://$SUBDOMAIN.$DOMAIN"
echo "https://admin.$SUBDOMAIN.$DOMAIN"
echo "https://api.$SUBDOMAIN.$DOMAIN"
