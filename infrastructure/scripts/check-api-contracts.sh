#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONTRACT_DIR="$ROOT/contracts"

if [[ ! -d "$CONTRACT_DIR" ]]; then
  echo "No contracts directory found."
  exit 1
fi

status=0
count=0

while IFS= read -r contract; do
  ((count+=1))
  version="$(awk -F': ' '/^version:/ {print $2}' "$contract" | tr -d '[:space:]')"
  name="$(awk -F': ' '/^name:/ {print $2}' "$contract" | tr -d '[:space:]')"

  if [[ -z "$name" ]]; then
    echo "❌ Missing name in $contract"
    status=1
  fi

  if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Invalid semantic version '$version' in $contract"
    status=1
  fi
done < <(find "$CONTRACT_DIR" -type f -name '*.contract.yaml' | sort)

if [[ "$count" -eq 0 ]]; then
  echo "❌ No contract files found in $CONTRACT_DIR"
  exit 1
fi

if [[ "$status" -ne 0 ]]; then
  exit "$status"
fi

echo "✅ Contract checks passed ($count files)."
