#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

status=0

check_k8s_file() {
  local file="$1"

  if ! grep -Eq '^[[:space:]]*resources:' "$file"; then
    echo "❌ Missing resources block: $file"
    status=1
  fi

  if ! grep -Eq '^[[:space:]]*image:[[:space:]]*[^[:space:]]+:[^[:space:]]+' "$file"; then
    echo "❌ Image tag is not pinned: $file"
    status=1
  fi

  if grep -Eq '^[[:space:]]*image:[[:space:]]*[^[:space:]]+:latest([[:space:]]|$)' "$file"; then
    echo "❌ Image uses forbidden latest tag: $file"
    status=1
  fi

  if ! grep -Eq 'runAsNonRoot:[[:space:]]*true' "$file"; then
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
