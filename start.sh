#!/usr/bin/env bash
set -euo pipefail

echo "Starting zTTato Platform (production profile)..."
docker compose pull
docker compose build --pull
docker compose up -d --remove-orphans

echo "Platform started."
docker compose ps
