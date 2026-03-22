#!/usr/bin/env bash
set -euo pipefail

if command -v gramine-sgx >/dev/null 2>&1; then
  exec gramine-sgx python src/main.py
fi

echo "gramine-sgx not found; falling back to standard python runtime" >&2
exec python src/main.py
