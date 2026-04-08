# Production Deployment Stack

This directory contains production-ready infrastructure definitions for the self-healing arbitrage control plane:

- `helm/zlttbots`: Kubernetes Helm chart with startup/readiness/liveness probes, HPA, PDB, ServiceMonitor, and NetworkPolicy.
- `argocd/apps/zlttbots-production.yaml`: Argo CD application for GitOps sync.

## Usage

```bash
helm template zlttbots deploy/helm/zlttbots
kubectl apply -f deploy/argocd/apps/zlttbots-production.yaml
```

For cluster bootstrapping via Terraform, see `infra/terraform/environments/production`.
