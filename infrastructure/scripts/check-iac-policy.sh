#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

status=0

check_k8s_file() {
  local file="$1"

  if ! rg -q '^\s*resources:' "$file"; then
    echo "❌ Missing resources block: $file"
    status=1
  fi

  if ! rg -q '^\s*image:\s*.+:.+' "$file"; then
    echo "❌ Image tag is not pinned: $file"
    status=1
  fi

  if ! rg -q 'runAsNonRoot:\s*true' "$file"; then
    echo "❌ Missing runAsNonRoot=true: $file"
    status=1
  fi
}

while IFS= read -r file; do
  check_k8s_file "$file"
done < <(find "$ROOT/infrastructure/k8s/deployments" -type f -name '*.yaml' | sort)

if [[ "$status" -ne 0 ]]; then
  exit "$status"
fi

echo "✅ IaC policy checks passed."
