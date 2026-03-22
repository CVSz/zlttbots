#!/usr/bin/env bash
set -Eeuo pipefail

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required" >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

cd "${TMP_DIR}"
curl -sL https://istio.io/downloadIstio | sh -
cd istio-*
export PATH="${PWD}/bin:${PATH}"

istioctl install --set profile=default -y
kubectl label namespace platform istio-injection=enabled --overwrite
kubectl apply -f "${REPO_ROOT}/infrastructure/k8s/enterprise/mesh/mtls-strict.yaml"
