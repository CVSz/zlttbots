#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ZTTATO_ROOT="$ROOT"
# shellcheck disable=SC1091
source "$ROOT/scripts/node-services-lib.sh"

printf '=================================\n'
printf 'Installing Node Services\n'
printf '=================================\n'

if ! command -v npm >/dev/null 2>&1; then
  printf 'ERROR: npm is required to install Node services.\n' >&2
  exit 1
fi

if [[ ${#ZTTATO_NODE_SERVICES[@]} -eq 0 ]]; then
  printf '[SKIP] No Node services with package.json were discovered under %s\n' "$ZTTATO_NODE_SERVICES_ROOT"
  exit 0
fi

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
