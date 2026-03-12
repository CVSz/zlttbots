#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "Bootstrapping platform..."

echo "Fixing shell permissions..."
find "$ROOT" -type f -name "*.sh" -exec chmod +x {} \;

echo ""
echo "Installing Node dependencies..."

NODE_PKGS=$(find "$ROOT/services" -maxdepth 2 -name package.json)

for pkg in $NODE_PKGS
do
  dir=$(dirname "$pkg")
  echo "npm install -> $dir"
  (cd "$dir" && npm install)
done

echo ""
echo "Installing Python dependencies..."

PY_PKGS=$(find "$ROOT/services" -maxdepth 2 -name requirements.txt)

for req in $PY_PKGS
do
  dir=$(dirname "$req")
  echo "pip install -> $dir"
  (cd "$dir" && pip install -r requirements.txt)
done

echo ""
echo "Starting Docker compose..."

cd "$ROOT"
docker compose up -d

echo "Bootstrap completed."
