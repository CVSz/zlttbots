#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
trap 'echo "Bootstrap failed at line ${LINENO}" >&2' ERR

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "Bootstrapping platform..."

echo "Fixing shell permissions..."
find "$ROOT/infrastructure/scripts" -type f -name "*.sh" -exec chmod 755 {} +

echo ""
echo "Installing Node dependencies..."

NODE_PKGS=$(find "$ROOT/services" -maxdepth 2 -type f -name package.json)

for pkg in $NODE_PKGS
do
  dir=$(dirname "$pkg")
  echo "npm ci -> $dir"
  (cd "$dir" && npm ci)
done

echo ""
echo "Installing Python dependencies..."

PY_PKGS=$(find "$ROOT/services" -maxdepth 2 -type f -name requirements.txt)

for req in $PY_PKGS
do
  dir=$(dirname "$req")
  echo "python -m pip install -> $dir"
  (cd "$dir" && python -m pip install --no-cache-dir -r requirements.txt)
done

echo ""
echo "Starting Docker compose..."

cd "$ROOT"
docker compose -f "$ROOT/docker-compose.yml" up -d --wait

echo "Bootstrap completed."
