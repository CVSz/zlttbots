#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
status=0

while IFS= read -r package; do
  package_dir="$(dirname "$package")"
  lockfile="$package_dir/package-lock.json"

  if [[ ! -f "$lockfile" ]]; then
    echo "Missing lockfile for $package_dir"
    status=1
    continue
  fi

  echo "Scanning $package_dir"
  (
    cd "$package_dir"
    npm audit --omit=dev --audit-level=high
  ) || status=1
done < <(
  {
    find "$ROOT" -maxdepth 1 -name package.json
    find "$ROOT/apps" -maxdepth 2 -name package.json
    find "$ROOT/services" -maxdepth 2 -name package.json
  } | sort -u
)

exit "$status"
