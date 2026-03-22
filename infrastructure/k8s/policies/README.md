# Cluster-wide policy enforcement (OPA Gatekeeper + Kyverno)

This folder defines admission policies for deployment safety controls:

- deny `:latest` image tags,
- require pod `securityContext.runAsNonRoot: true`,
- require container cpu/memory requests and limits,
- enforce image repository allowlist for deployments.

## Prerequisites

Install policy engines first:

- OPA Gatekeeper (for `ConstraintTemplate` and `Constraint` resources)
- Kyverno (for `ClusterPolicy` resources)

## Apply

```bash
kubectl apply -k infrastructure/k8s/policies
```

## CI/Pre-merge

Keep local checks aligned with admission policies:

```bash
bash infrastructure/scripts/check-iac-policy.sh
```
