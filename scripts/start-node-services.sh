#!/usr/bin/env bash

set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICES="$ROOT/services"

echo "================================="
echo "Installing Node Dependencies"
echo "================================="

for dir in \
  shopee-crawler \
  tiktok-uploader \
  tiktok-shop-miner \
  tiktok-farm \
  account-farm \
  analytics \
  admin-panel \
  ai-video-generator \
  click-tracker
do
  echo "Installing dependencies -> $dir"
  cd "$SERVICES/$dir"
  npm install --production
done

echo "================================="
echo "Starting Node Services via PM2"
echo "================================="

cd "$ROOT"

pm2 start ecosystem.config.js
pm2 save

echo "================================="
echo "Node Services Running"
echo "================================="

pm2 list
