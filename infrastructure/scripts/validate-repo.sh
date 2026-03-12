#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "--------------------------------"
echo "Repository Validation"
echo "--------------------------------"

echo ""
echo "Dockerfiles:"
find "$ROOT" -name Dockerfile

echo ""
echo "Node services:"
find "$ROOT/services" -name package.json

echo ""
echo "Python services:"
find "$ROOT/services" -name requirements.txt

echo ""
echo "Shell scripts:"
find "$ROOT" -name "*.sh"

echo ""
echo "Kubernetes manifests:"
find "$ROOT/infrastructure/k8s" -name "*.yaml"

echo ""
echo "Validation completed."
