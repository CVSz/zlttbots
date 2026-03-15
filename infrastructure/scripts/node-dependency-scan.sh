#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
status=0

while IFS= read -r package; do
  service_dir="$(dirname "$package")"
  echo "Scanning $service_dir"
  (
    cd "$service_dir"
    npm audit --omit=dev --audit-level=high
  ) || status=1
done < <(find "$ROOT/services" -maxdepth 2 -name package.json | sort)

exit "$status"
