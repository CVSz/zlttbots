#!/usr/bin/env bash
set -e

CONTAINERS=(
zlttbots-postgres-1
zlttbots-redis-1
)

for c in "${CONTAINERS[@]}"
do

if ! docker ps | grep -q "$c"; then

echo "[docker-recovery] restarting $c"

docker restart "$c"

fi

done
