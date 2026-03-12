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
