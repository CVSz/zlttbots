#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=/dev/null
source "$ROOT_DIR/env"

TUNNEL_ID="${1:-${CF_TUNNEL_ID:-}}"
RECORD_NAME="${2:-${SUBDOMAIN:-}}"

if [[ -z "$TUNNEL_ID" ]]; then
  echo "Missing tunnel id argument or CF_TUNNEL_ID in cloudflare-devops/env" >&2
  exit 1
fi

if [[ -z "$RECORD_NAME" ]]; then
  echo "Missing DNS record name argument or SUBDOMAIN in cloudflare-devops/env" >&2
  exit 1
fi

curl -s -X POST \
"https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records" \
-H "Authorization: Bearer $CF_API_TOKEN" \
-H "Content-Type: application/json" \
--data "{\"type\":\"CNAME\",\"name\":\"$RECORD_NAME\",\"content\":\"$TUNNEL_ID.cfargotunnel.com\",\"ttl\":1,\"proxied\":true}"
