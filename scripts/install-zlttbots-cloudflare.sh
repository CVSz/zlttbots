# path: scripts/install-zlttbots-cloudflare.sh
#!/usr/bin/env bash

set -Eeuo pipefail

DOMAIN="zeaz.dev"
TUNNEL_NAME="zlttbots"
ROOT="$(pwd)"
CF_DIR="/root/.cloudflared"

echo "===================================="
echo "zlttbots Cloudflare Tunnel Installer"
echo "===================================="

########################################
# install cloudflared
########################################

if ! command -v cloudflared >/dev/null 2>&1; then

echo "Installing cloudflared..."

curl -L \
https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
-o /usr/local/bin/cloudflared

chmod +x /usr/local/bin/cloudflared

fi

########################################
# login
########################################

echo "Cloudflare login..."

cloudflared tunnel login

########################################
# create tunnel
########################################

mkdir -p "$CF_DIR"

echo "Creating tunnel..."

cloudflared tunnel create "$TUNNEL_NAME"

TUNNEL_ID=$(ls $CF_DIR/*.json | head -n1 | xargs basename | sed 's/.json//')

echo "Tunnel ID: $TUNNEL_ID"

########################################
# DNS routes
########################################

echo "Creating DNS routes..."

cloudflared tunnel route dns "$TUNNEL_NAME" "zlttbots.$DOMAIN"
cloudflared tunnel route dns "$TUNNEL_NAME" "*.zlttbots.$DOMAIN"

########################################
# generate config
########################################

CONFIG="$CF_DIR/config.yml"

echo "Generating config..."

cat > "$CONFIG" <<EOF
tunnel: $TUNNEL_ID
credentials-file: $CF_DIR/$TUNNEL_ID.json

ingress:

  - hostname: zlttbots.$DOMAIN
    service: http://admin-panel:3000

  - hostname: api.zlttbots.$DOMAIN
    service: http://analytics:9100

  - hostname: video.zlttbots.$DOMAIN
    service: http://ai-video-generator:9400

  - hostname: arbitrage.zlttbots.$DOMAIN
    service: http://arbitrage-engine:9500

  - hostname: crawler.zlttbots.$DOMAIN
    service: http://market-crawler:9200

  - hostname: "*.zlttbots.$DOMAIN"
    service: http://admin-panel:3000

  - service: http_status:404
EOF

########################################
# generate docker service
########################################

echo "Generating docker-compose.cloudflare.yml..."

cat > docker-compose.cloudflare.yml <<EOF
services:

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: zlttbots-cloudflared
    restart: unless-stopped
    command: tunnel run $TUNNEL_ID
    volumes:
      - $CF_DIR:/etc/cloudflared
    networks:
      - default
EOF

########################################
# start cloudflare tunnel
########################################

echo "Starting cloudflare tunnel..."

docker compose -f docker-compose.yml -f docker-compose.cloudflare.yml up -d

########################################
# summary
########################################

echo ""
echo "===================================="
echo "Cloudflare Tunnel Installed"
echo "===================================="
echo ""

echo "Domains:"

echo "https://zlttbots.$DOMAIN"
echo "https://api.zlttbots.$DOMAIN"
echo "https://video.zlttbots.$DOMAIN"
echo "https://arbitrage.zlttbots.$DOMAIN"
echo "https://crawler.zlttbots.$DOMAIN"

echo ""
echo "Tunnel running via Docker"
echo "===================================="
