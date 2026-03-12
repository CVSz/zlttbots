# Kubernetes Deployment

Deploy all manifests from the infrastructure folder.

```bash
kubectl apply -f infrastructure/k8s
```

Enable autoscaling for worker-heavy services where needed.
