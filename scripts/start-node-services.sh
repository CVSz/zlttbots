#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ECOSYSTEM_CONFIG="$REPO_ROOT/ecosystem.config.js"
LOG_DIR="$REPO_ROOT/logs/node"

mkdir -p "$LOG_DIR"

echo "================================="
echo "Starting Node Services with PM2"
echo "Repo: $REPO_ROOT"
echo "================================="

if [ ! -f "$ECOSYSTEM_CONFIG" ]; then
  echo "ERROR: ecosystem config not found at $ECOSYSTEM_CONFIG"
  exit 1
fi

if ! command -v pm2 >/dev/null 2>&1; then
  echo "PM2 not found. Installing globally..."
  npm install -g pm2
fi

echo "Installing npm dependencies for Node services..."
while IFS= read -r package_file; do
  service_dir="$(dirname "$package_file")"
  echo "Installing dependencies -> $(basename "$service_dir")"
  pushd "$service_dir" >/dev/null

  if [ -f package-lock.json ]; then
    npm ci
  else
    npm install
  fi

  popd >/dev/null
done < <(find "$REPO_ROOT/services" -mindepth 2 -maxdepth 2 -name package.json | sort)

echo "Starting PM2 processes from $ECOSYSTEM_CONFIG"
pm2 start "$ECOSYSTEM_CONFIG"
pm2 save
pm2 list

echo ""
echo "================================="
echo "Node Services Started via PM2"
echo "PM2 logs: pm2 logs"
echo "================================="
