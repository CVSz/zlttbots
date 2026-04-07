#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "Building all Docker images..."

DOCKERFILES=$(find "$ROOT/services" -name Dockerfile)

for df in $DOCKERFILES
do
  dir=$(dirname "$df")
  service=$(basename "$(dirname "$dir")")

  echo "Building image: $service"
  docker build -t zlttbots/$service "$dir"
done

echo "Build complete."
