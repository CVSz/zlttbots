#!/usr/bin/env bash

set -e

echo "Starting zTTato Enterprise Platform"

docker compose -f docker-compose.enterprise.yml up -d

sleep 10

docker ps
