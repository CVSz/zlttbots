# Enterprise Cluster Mode Runbook

This runbook provides a production deployment path for enterprise cluster mode (HA data plane, autoscaling, policy enforcement, and strict mTLS).

## Included assets

- `infrastructure/k8s/enterprise/` kustomize stack:
  - external secret sync,
  - Postgres HA statefulset,
  - Redpanda statefulset,
  - model-service deployment/service,
  - HPA + KEDA autoscale,
  - ingress,
  - strict mTLS policy,
  - Prometheus additional scrape config.
- `infrastructure/k8s/policies/` admission policies (Gatekeeper + Kyverno).
- scripts:
  - `scripts/k8s-bootstrap.sh`
  - `scripts/install-istio.sh`
  - `scripts/k8s-deploy-enterprise.sh`

## Prerequisites

1. Kubernetes cluster initialized (`kubeadm` or managed cluster).
2. External Secrets Operator installed with `ClusterSecretStore` named `zttato-secret-store`.
3. KEDA installed.
4. Istio installed (or install via `scripts/install-istio.sh`).
5. Gatekeeper and Kyverno installed (for policy enforcement).

## Bootstrap and deploy

```bash
# control plane bootstrap (new self-managed cluster)
sudo bash scripts/k8s-bootstrap.sh

# install istio + strict mTLS for platform namespace
bash scripts/install-istio.sh

# deploy policy pack + enterprise stack
bash scripts/k8s-deploy-enterprise.sh
```

## Post-deploy checks

```bash
kubectl get pods -n platform
kubectl get hpa -n platform
kubectl get scaledobjects.keda.sh -n platform
kubectl get externalsecret -n platform
```

## Operational guarantees

- no `:latest` deployment images in enforced paths,
- mandatory cpu/memory requests and limits,
- mandatory pod `runAsNonRoot: true`,
- strict mTLS in namespace `platform`,
- policy enforcement at admission layer plus pre-merge script checks.
