# path: scripts/regen-cloudflare-devops-toolkit.sh
#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="$(pwd)"
TOOLKIT="$ROOT/cloudflare-devops"

echo "======================================"
echo "Rebuilding Cloudflare DevOps Toolkit"
echo "======================================"

rm -rf "$TOOLKIT"

mkdir -p "$TOOLKIT"/{api,tunnel,docker}

########################################
# ENV
########################################

cat > "$TOOLKIT/env.example" <<'EOF'
CF_API_TOKEN=
CF_ACCOUNT_ID=
CF_ZONE_ID=

DOMAIN=zeaz.dev
SUBDOMAIN=zttato

# generated automatically
CF_TUNNEL_TOKEN=
EOF

########################################
# create tunnel
########################################

cat > "$TOOLKIT/api/create-tunnel.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$ROOT_DIR/env"

SECRET=$(openssl rand -base64 32)

curl -s -X POST \
"https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel" \
-H "Authorization: Bearer $CF_API_TOKEN" \
-H "Content-Type: application/json" \
--data "{\"name\":\"$SUBDOMAIN\",\"tunnel_secret\":\"$SECRET\"}"
EOF

########################################
# create dns
########################################

cat > "$TOOLKIT/api/create-dns.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$ROOT_DIR/env"

TUNNEL_ID=$1

curl -s -X POST \
"https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records" \
-H "Authorization: Bearer $CF_API_TOKEN" \
-H "Content-Type: application/json" \
--data "{\"type\":\"CNAME\",\"name\":\"$SUBDOMAIN\",\"content\":\"$TUNNEL_ID.cfargotunnel.com\",\"ttl\":1,\"proxied\":true}"
EOF

########################################
# docker cloudflared
########################################

cat > "$TOOLKIT/docker/docker-compose.cloudflare.yml" <<'EOF'
services:

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: zttato-cloudflared
    restart: unless-stopped
    command: tunnel run --token ${CF_TUNNEL_TOKEN}
EOF

########################################
# installer
########################################

cat > "$TOOLKIT/install.sh" <<'EOF'
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
EOF

chmod +x "$TOOLKIT"/api/*.sh
chmod +x "$TOOLKIT"/install.sh

echo ""
echo "======================================"
echo "Toolkit regenerated successfully"
echo "======================================"

echo ""
echo "Next steps:"
echo ""
echo "cd cloudflare-devops"
echo "cp env.example env"
echo "nano env"
echo ""
echo "bash install.sh"
