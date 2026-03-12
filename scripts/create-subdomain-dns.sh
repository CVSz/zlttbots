# path: scripts/create-subdomain-dns.sh
#!/usr/bin/env bash

set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

source cloudflare-devops/env

TUNNEL_ID="65ce97ea-792b-41ad-bf00-43d222b00798"

SUBS=("api" "gpu" "predict")

for SUB in "${SUBS[@]}"; do

curl -s -X POST \
"https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records" \
-H "Authorization: Bearer $CF_API_TOKEN" \
-H "Content-Type: application/json" \
--data "{
\"type\":\"CNAME\",
\"name\":\"$SUB.$SUBDOMAIN\",
\"content\":\"$TUNNEL_ID.cfargotunnel.com\",
\"proxied\":true,
\"ttl\":1
}"

echo "Created DNS: $SUB.$SUBDOMAIN.$DOMAIN"

done
