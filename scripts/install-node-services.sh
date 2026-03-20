#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ZTTATO_ROOT="$ROOT"
# shellcheck disable=SC1091
source "$ROOT/scripts/node-services-lib.sh"

printf '=================================\n'
printf 'Installing Node Services\n'
printf '=================================\n'

for service in "${ZTTATO_NODE_SERVICES[@]}"; do
  dir="$(zttato_node_service_dir "$service")"
  package_json="$(zttato_node_service_package "$service")"

  if [[ ! -d "$dir" ]]; then
    printf '[SKIP] %s (directory not found)\n' "$service"
    continue
  fi

  if [[ ! -f "$package_json" ]]; then
    printf '[SKIP] %s (no package.json)\n' "$service"
    continue
  fi

  printf '[INSTALL] %s\n' "$service"

  (
    cd "$dir"

    if [[ -f package-lock.json ]]; then
      npm ci --silent
    else
      npm install --silent
    fi
  )
done

printf '✅ Node services installed\n'
