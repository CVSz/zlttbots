#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "Starting development cluster..."

cd "$ROOT"
docker compose up -d

echo "Cluster running."
