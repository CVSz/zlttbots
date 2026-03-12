# path: scripts/regen-cloudflare-devops-toolkit.sh
#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="$(pwd)"
TOOLKIT="$ROOT/cloudflare-devops"

echo "======================================"
echo "Regenerating Cloudflare DevOps Toolkit"
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
# tunnel config
########################################

cat > "$TOOLKIT/tunnel/generate-config.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

TUNNEL_ID=$1

cat <<CONFIG
tunnel: $TUNNEL_ID

ingress:

  - hostname: admin.zttato.zeaz.dev
    service: http://admin-panel:3000

  - hostname: api.zttato.zeaz.dev
    service: http://analytics:9100

  - hostname: video.zttato.zeaz.dev
    service: http://ai-video-generator:9400

  - hostname: arb.zttato.zeaz.dev
    service: http://arbitrage-engine:9500

  - hostname: crawler.zttato.zeaz.dev
    service: http://market-crawler:9200

  - service: http_status:404
CONFIG
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
    sudo apt install jq -y
fi

if ! command -v cloudflared >/dev/null 2>&1; then

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

echo "CF_TUNNEL_TOKEN=$TOKEN" >> "$ROOT/env"

########################################
# create dns
########################################

echo "Creating DNS..."

bash api/create-dns.sh "$TUNNEL_ID"

########################################
# start docker tunnel
########################################

docker compose \
-f ../docker-compose.yml \
-f docker/docker-compose.cloudflare.yml up -d

echo ""
echo "================================"
echo "Edge tunnel deployed"
echo "================================"

echo "Domains:"
echo "https://admin.zttato.$DOMAIN"
echo "https://api.zttato.$DOMAIN"
EOF

chmod +x "$TOOLKIT"/api/*.sh
chmod +x "$TOOLKIT"/tunnel/*.sh
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
