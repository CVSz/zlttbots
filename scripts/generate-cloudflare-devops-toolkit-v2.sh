# path: scripts/generate-cloudflare-devops-toolkit-v2.sh
#!/usr/bin/env bash
#
# Cloudflare API DevOps Toolkit v2
# Generates a production-ready toolkit to:
# - create / reuse Cloudflare Tunnel via API
# - fetch tunnel token
# - configure ingress routing
# - create DNS records
# - run cloudflared via Docker
#
# Usage:
#   bash scripts/generate-cloudflare-devops-toolkit-v2.sh

set -Eeuo pipefail

ROOT="$(pwd)"
TOOLKIT="$ROOT/cloudflare-devops-v2"

echo "======================================"
echo "Generating Cloudflare API DevOps Toolkit v2"
echo "Root: $TOOLKIT"
echo "======================================"

rm -rf "$TOOLKIT"

mkdir -p "$TOOLKIT"/{api,config,docker}

########################################
# ENV
########################################

cat > "$TOOLKIT/env.example" <<'EOF'
CF_API_TOKEN=
CF_ACCOUNT_ID=
CF_ZONE_ID=

DOMAIN=zeaz.dev
SUBDOMAIN=zttato

TUNNEL_NAME=zttato
EOF

########################################
# list tunnels
########################################

cat > "$TOOLKIT/api/list-tunnels.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

source "$(dirname "$0")/../env"

curl -s \
https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel \
-H "Authorization: Bearer $CF_API_TOKEN" \
-H "Content-Type: application/json"
EOF

########################################
# create tunnel
########################################

cat > "$TOOLKIT/api/create-tunnel.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

source "$(dirname "$0")/../env"

SECRET=$(openssl rand -base64 32)

curl -s -X POST \
https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel \
-H "Authorization: Bearer $CF_API_TOKEN" \
-H "Content-Type: application/json" \
-d '{
"name":"'"$TUNNEL_NAME"'",
"tunnel_secret":"'"$SECRET"'",
"config_src":"cloudflare"
}'
EOF

########################################
# get token
########################################

cat > "$TOOLKIT/api/get-token.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

source "$(dirname "$0")/../env"

TUNNEL_ID="$1"

curl -s \
https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID/token \
-H "Authorization: Bearer $CF_API_TOKEN"
EOF

########################################
# configure ingress
########################################

cat > "$TOOLKIT/api/configure-ingress.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

source "$(dirname "$0")/../env"

TUNNEL_ID="$1"

curl -s -X PUT \
https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID/configurations \
-H "Authorization: Bearer $CF_API_TOKEN" \
-H "Content-Type: application/json" \
-d '{
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
"service":"http_status:404"
}
]
}
}'
EOF

########################################
# create dns
########################################

cat > "$TOOLKIT/api/create-dns.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

source "$(dirname "$0")/../env"

TUNNEL_ID="$1"

curl -s -X POST \
https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records \
-H "Authorization: Bearer $CF_API_TOKEN" \
-H "Content-Type: application/json" \
-d '{
"type":"CNAME",
"name":"'"$SUBDOMAIN"'",
"content":"'"$TUNNEL_ID"'.cfargotunnel.com",
"proxied":true,
"ttl":1
}'
EOF

########################################
# docker compose
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

cd "$ROOT"

source env

echo "================================"
echo "Cloudflare DevOps Toolkit v2"
echo "================================"

########################################
# dependencies
########################################

if ! command -v jq >/dev/null 2>&1; then
    sudo apt update
    sudo apt install jq -y
fi

########################################
# detect existing tunnel
########################################

echo "Checking tunnels..."

TUNNEL_ID=$(bash api/list-tunnels.sh \
| jq -r '.result[] | select(.name=="'"$TUNNEL_NAME"'") | .id')

if [ -z "$TUNNEL_ID" ]; then

echo "Creating tunnel..."

RESPONSE=$(bash api/create-tunnel.sh)

SUCCESS=$(echo "$RESPONSE" | jq -r '.success')

if [ "$SUCCESS" != "true" ]; then
    echo "$RESPONSE"
    exit 1
fi

TUNNEL_ID=$(echo "$RESPONSE" | jq -r '.result.id')

fi

echo "Tunnel ID: $TUNNEL_ID"

########################################
# get token
########################################

TOKEN=$(bash api/get-token.sh "$TUNNEL_ID" \
| jq -r '.result')

echo "CF_TUNNEL_TOKEN=$TOKEN" >> env

export CF_TUNNEL_TOKEN="$TOKEN"

########################################
# configure ingress
########################################

echo "Configuring ingress..."

bash api/configure-ingress.sh "$TUNNEL_ID"

########################################
# create DNS
########################################

echo "Creating DNS..."

bash api/create-dns.sh "$TUNNEL_ID"

########################################
# run tunnel
########################################

docker compose \
-f ../docker-compose.yml \
-f docker/docker-compose.cloudflare.yml \
up -d

echo ""
echo "================================"
echo "Cloudflare Edge deployed"
echo "================================"

echo "https://$SUBDOMAIN.$DOMAIN"
echo "https://api.$SUBDOMAIN.$DOMAIN"
echo "https://gpu.$SUBDOMAIN.$DOMAIN"
EOF

########################################
# permissions
########################################

chmod +x "$TOOLKIT"/api/*.sh
chmod +x "$TOOLKIT/install.sh"

echo ""
echo "======================================"
echo "Cloudflare DevOps Toolkit v2 created"
echo "======================================"

echo ""
echo "Next steps:"
echo ""
echo "cd cloudflare-devops-v2"
echo "cp env.example env"
echo "nano env"
echo ""
echo "bash install.sh"
