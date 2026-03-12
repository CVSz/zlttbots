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
