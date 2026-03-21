#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

require_cmd kubectl
require_cmd bash
require_cmd npx

if [[ ! -f cloudflare-devops/env ]]; then
  echo "Missing cloudflare-devops/env" >&2
  exit 1
fi

# shellcheck source=/dev/null
source cloudflare-devops/env

echo "Deploy multi-region K8s..."
kubectl apply -f infrastructure/k8s/multi-region/asia.yaml
kubectl apply -f infrastructure/k8s/multi-region/eu.yaml

echo "Deploy Cloudflare tunnel..."
bash cloudflare-devops/install.sh

# shellcheck source=/dev/null
source cloudflare-devops/env

echo "Deploy DNS wildcard..."
bash cloudflare-devops/api/create-dns.sh "${CF_TUNNEL_ID:-${1:-}}" "*.zeaz.dev"

echo "Deploy edge worker..."
npx wrangler deploy --config services/edge-worker/wrangler.toml

echo "DONE: Global system live"
