#!/usr/bin/env bash

echo "zlttbots diagnostics"

echo
echo "Docker containers"

docker ps

echo
echo "Services"

curl -s localhost:9100/docs >/dev/null && echo "viral OK"
curl -s localhost:9400/docs >/dev/null && echo "crawler OK"
curl -s localhost:9500/docs >/dev/null && echo "arbitrage OK"
curl -s localhost:9300/docs >/dev/null && echo "renderer OK"

echo
echo "Edge"

curl -I https://api.zeaz.dev || true
curl -I https://gpu.zeaz.dev || true
curl -I https://predict.zeaz.dev || true

echo
echo "Node Services"

for svc in services/*
do

if [ -f "$svc/package.json" ]; then

NAME=$(basename "$svc")

PORT=$(grep PORT "$svc/.env" 2>/dev/null | cut -d= -f2 || true)

if [ -n "$PORT" ]; then

curl -s "http://localhost:$PORT/health" >/dev/null \
&& echo "$NAME OK" \
|| echo "$NAME FAIL"

fi

fi

done
