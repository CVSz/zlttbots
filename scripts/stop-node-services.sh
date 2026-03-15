#!/usr/bin/env bash

set -euo pipefail

echo "Stopping Node services managed by PM2..."

if command -v pm2 >/dev/null 2>&1; then
  pm2 delete all || true
  pm2 save || true
else
  echo "PM2 is not installed; nothing to stop via PM2."
fi

echo "Done."
