#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$ROOT/env"
ENV_TEMPLATE="$ROOT/env.example"

if [[ ! -f "$ENV_FILE" ]]; then
    if [[ -f "$ENV_TEMPLATE" ]]; then
        cp "$ENV_TEMPLATE" "$ENV_FILE"
        echo "Created $ENV_FILE from env.example. Fill required values and rerun."
    else
        echo "Missing $ENV_FILE and $ENV_TEMPLATE"
    fi
    exit 1
fi

# shellcheck source=/dev/null
source "$ENV_FILE"

echo "================================"
echo "Cloudflare Edge Installer"
echo "================================"

required_vars=(CF_API_TOKEN CF_ACCOUNT_ID CF_ZONE_ID DOMAIN SUBDOMAIN)
for var in "${required_vars[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        echo "Missing required variable in $(basename "$ENV_FILE"): $var"
        exit 1
    fi
done

echo "Installer configuration check passed. Approved to run."

########################################
# dependencies
########################################

if ! command -v jq >/dev/null 2>&1; then
    sudo apt update
    sudo apt install jq -y
fi

if ! command -v cloudflared >/dev/null 2>&1; then
    echo "Installing cloudflared..."
    curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
        -o /tmp/cloudflared
    sudo install -m 0755 /tmp/cloudflared /usr/local/bin/cloudflared
    rm -f /tmp/cloudflared
fi

########################################
# create tunnel
########################################

echo "Creating tunnel..."
RESPONSE="$(bash "$ROOT/api/create-tunnel.sh")"
SUCCESS="$(echo "$RESPONSE" | jq -r '.success')"

if [[ "$SUCCESS" != "true" ]]; then
    echo "$RESPONSE"
    echo "Tunnel creation failed"
    exit 1
fi

TUNNEL_ID="$(echo "$RESPONSE" | jq -r '.result.id')"
TOKEN="$(echo "$RESPONSE" | jq -r '.result.token')"

echo "Tunnel ID: $TUNNEL_ID"

########################################
# save token
########################################

grep -Ev '^(CF_TUNNEL_TOKEN|CF_TUNNEL_ID)=' "$ENV_FILE" > "$ENV_FILE.tmp" || true
mv "$ENV_FILE.tmp" "$ENV_FILE"
echo "CF_TUNNEL_ID=$TUNNEL_ID" >> "$ENV_FILE"
echo "CF_TUNNEL_TOKEN=$TOKEN" >> "$ENV_FILE"

########################################
# create dns
########################################

echo "Creating DNS..."
bash "$ROOT/api/create-dns.sh" "$TUNNEL_ID"

########################################
# export env
########################################

set -a
# shellcheck source=/dev/null
source "$ENV_FILE"
set +a

########################################
# start docker tunnel
########################################

docker compose \
    -f "$ROOT/../docker-compose.yml" \
    -f "$ROOT/docker/docker-compose.cloudflare.yml" \
    up -d

echo ""
echo "================================"
echo "Cloudflare Tunnel Running"
echo "================================"
echo "https://$SUBDOMAIN.$DOMAIN"
echo "https://admin.$SUBDOMAIN.$DOMAIN"
echo "https://api.$SUBDOMAIN.$DOMAIN"
