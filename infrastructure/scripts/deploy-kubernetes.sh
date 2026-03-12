#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "Deploying Kubernetes resources..."

kubectl apply -f "$ROOT/infrastructure/k8s/config"
kubectl apply -f "$ROOT/infrastructure/k8s/base"
kubectl apply -f "$ROOT/infrastructure/k8s/services"
kubectl apply -f "$ROOT/infrastructure/k8s/deployments"
kubectl apply -f "$ROOT/infrastructure/k8s/autoscale"
kubectl apply -f "$ROOT/infrastructure/k8s/ingress"

echo "Deployment complete."
