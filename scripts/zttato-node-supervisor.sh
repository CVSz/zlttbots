#!/usr/bin/env bash

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

while true
do

for svc in "$ROOT/services/"*
do

if [ -f "$svc/package.json" ]; then

PORT=$(grep PORT "$svc/.env" 2>/dev/null | cut -d= -f2 || true)

if [ -n "$PORT" ]; then

if ! lsof -i:$PORT >/dev/null 2>&1; then

echo "[node-supervisor] restarting $(basename $svc)"

cd "$svc"
npm run start &

fi

fi

fi

done

sleep 10

done

