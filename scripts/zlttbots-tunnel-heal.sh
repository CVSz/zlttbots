#!/usr/bin/env bash
set -e

if ! docker ps | grep -q zlttbots-cloudflared; then

echo "[tunnel-heal] restarting tunnel"

docker restart zlttbots-cloudflared || docker start zlttbots-cloudflared

fi
