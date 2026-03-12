#!/usr/bin/env bash
set -e

if ! docker ps | grep -q zttato-cloudflared; then

echo "[tunnel-heal] restarting tunnel"

docker restart zttato-cloudflared || docker start zttato-cloudflared

fi
