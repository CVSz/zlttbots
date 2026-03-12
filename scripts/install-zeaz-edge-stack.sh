# scripts/install-zeaz-edge-stack.sh
#!/usr/bin/env bash
set -Eeuo pipefail

# ==========================================
# ZEAZ EDGE STACK INSTALLER
# Cloudflare Tunnel + Docker Platform
# ==========================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CF_DIR="cloudflare-devops"
cd "$ROOT_DIR/$CF_DIR"

echo "======================================"
echo "ZEAZ EDGE STACK INSTALLER"
echo "Root: $ROOT_DIR/$CF_DIR"
echo "======================================"

# ------------------------------------------------
# Load environment
# ------------------------------------------------

if [[ -f "$ROOT_DIR/$CF_DIR/env" ]]; then
    set -a
    source "$ROOT_DIR/$CF_DIR/env"
    set +a
fi

if [[ -z "${CF_API_TOKEN:-}" ]]; then
    echo "ERROR: CF_API_TOKEN missing"
    exit 1
fi

if [[ -z "${CF_ACCOUNT_ID:-}" ]]; then
    echo "ERROR: CF_ACCOUNT_ID missing"
    exit 1
fi

if [[ -z "${CF_ZONE_ID:-}" ]]; then
    echo "ERROR: CF_ZONE_ID missing"
    exit 1
fi

# ------------------------------------------------
# Kernel tuning (Cloudflare QUIC performance)
# ------------------------------------------------

echo
echo "Configuring kernel network buffers"

sysctl -w net.core.rmem_max=7500000 >/dev/null
sysctl -w net.core.wmem_max=7500000 >/dev/null
sysctl -w net.core.netdev_max_backlog=4096 >/dev/null

grep -q net.core.rmem_max /etc/sysctl.conf || echo "net.core.rmem_max=7500000" >> /etc/sysctl.conf
grep -q net.core.wmem_max /etc/sysctl.conf || echo "net.core.wmem_max=7500000" >> /etc/sysctl.conf

# ------------------------------------------------
# Create or fetch Cloudflare Tunnel
# ------------------------------------------------

echo
echo "Checking existing tunnel"

TUNNEL_NAME="zeaz-edge"
if [[ -z "$CF_TUNNEL_TOKEN" || "$CF_TUNNEL_TOKEN" == "null" ]]; then
    echo "ERROR: Failed to fetch tunnel token"
    exit 1
fi

TUNNEL_ID=$(curl -s \
"https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel" \
-H "Authorization: Bearer $CF_API_TOKEN" | jq -r ".result[] | select(.name==\"$TUNNEL_NAME\") | .id")

if [[ -z "$TUNNEL_ID" || "$TUNNEL_ID" == "null" ]]; then

    echo "Creating new tunnel"

    TUNNEL_ID=$(curl -s -X POST \
    "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel" \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -H "Content-Type: application/json" \
    --data "{\"name\":\"$TUNNEL_NAME\",\"config_src\":\"cloudflare\"}" \
    | jq -r '.result.id')

fi

echo "Tunnel ID: $TUNNEL_ID"

# ------------------------------------------------
# Fetch Tunnel Token
# ------------------------------------------------

echo
echo "Fetching tunnel token"

CF_TUNNEL_TOKEN=$(curl -s \
"https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID/token" \
-H "Authorization: Bearer $CF_API_TOKEN" | jq -r '.result')

# ------------------------------------------------
# Save env
# ------------------------------------------------

echo
echo "Saving environment"

cat > "$ROOT_DIR/env.edge" <<EOF
CF_TUNNEL_ID=$TUNNEL_ID
CF_TUNNEL_TOKEN=$CF_TUNNEL_TOKEN
EOF

# ------------------------------------------------
# Configure Tunnel ingress
# ------------------------------------------------

echo
echo "Updating tunnel ingress"

cat > /tmp/tunnel-config.json <<EOF
{
  "config": {
    "ingress": [
      {
        "hostname": "zttato.zeaz.dev",
        "service": "http://market-crawler:9400"
      },
      {
        "hostname": "api.zeaz.dev",
        "service": "http://arbitrage-engine:9500"
      },
      {
        "hostname": "gpu.zeaz.dev",
        "service": "http://gpu-renderer:9300"
      },
      {
        "hostname": "predict.zeaz.dev",
        "service": "http://viral-predictor:9100"
      },
      {
        "service": "http_status:404"
      }
    ]
  }
}
EOF

curl -s -X PUT \
"https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID/configurations" \
-H "Authorization: Bearer $CF_API_TOKEN" \
-H "Content-Type: application/json" \
--data @/tmp/tunnel-config.json >/dev/null

# ------------------------------------------------
# Ensure DNS records
# ------------------------------------------------

echo
echo "Ensuring DNS records"

create_dns() {

    local host=$1

    exists=$(curl -s \
    "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records?name=$host" \
    -H "Authorization: Bearer $CF_API_TOKEN" | jq '.result | length')

    if [[ "$exists" -eq 0 ]]; then

        echo "Creating DNS: $host"

        curl -s -X POST \
        "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json" \
        --data "{
          \"type\":\"CNAME\",
          \"name\":\"$host\",
          \"content\":\"$TUNNEL_ID.cfargotunnel.com\",
          \"proxied\":true
        }" >/dev/null

    else
        echo "DNS exists: $host"
    fi
}

create_dns "zttato.zeaz.dev"
create_dns "api.zeaz.dev"
create_dns "gpu.zeaz.dev"
create_dns "predict.zeaz.dev"

# ------------------------------------------------
# Deploy Docker platform
# ------------------------------------------------

echo
echo "Deploying docker stack"

docker compose down --remove-orphans || true

docker compose build --parallel

docker compose up -d

sleep 5

# ------------------------------------------------
# Run cloudflared container
# ------------------------------------------------

echo
echo "Starting cloudflared"

docker rm -f zttato-cloudflared >/dev/null 2>&1 || true

docker run -d \
--name zttato-cloudflared \
--network zttato-platform_default \
--restart unless-stopped \
cloudflare/cloudflared:latest \
tunnel --no-autoupdate run --token "$CF_TUNNEL_TOKEN"

sleep 3

# ------------------------------------------------
# Warm Cloudflare Edge
# ------------------------------------------------

echo
echo "Warming TLS edge"

for d in \
zttato.zeaz.dev \
api.zeaz.dev \
gpu.zeaz.dev \
predict.zeaz.dev
do
    curl -ks https://$d >/dev/null || true
done

# ------------------------------------------------
# Verify endpoints
# ------------------------------------------------

echo
echo "Verifying endpoints"

for d in \
zttato.zeaz.dev \
api.zeaz.dev \
gpu.zeaz.dev \
predict.zeaz.dev
do
    code=$(curl -ks -o /dev/null -w "%{http_code}" https://$d)
    echo "$d → HTTP $code"
done

# ------------------------------------------------
# Status
# ------------------------------------------------

echo
echo "======================================"
echo "ZEAZ EDGE STACK INSTALLED"
echo "======================================"

echo
echo "Endpoints:"
echo "https://zttato.zeaz.dev"
echo "https://api.zeaz.dev"
echo "https://gpu.zeaz.dev"
echo "https://predict.zeaz.dev"

echo
echo "Swagger:"
echo "https://api.zeaz.dev/docs"
echo "https://gpu.zeaz.dev/docs"
echo "https://predict.zeaz.dev/docs"

echo
echo "Tunnel logs:"
echo "docker logs -f zttato-cloudflared"

echo
echo "Diagnostics:"
echo "bash scripts/zttato-edge-doctor.sh"
