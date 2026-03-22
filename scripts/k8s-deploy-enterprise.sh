#!/usr/bin/env bash
set -Eeuo pipefail

if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl is required" >&2
  exit 1
fi

kubectl apply -k infrastructure/k8s/policies
kubectl apply -k infrastructure/k8s/enterprise

echo "Deployment applied. Current pods:"
kubectl get pods -n platform
