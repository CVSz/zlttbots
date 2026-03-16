# CI/CD

Automated pipeline tasks include:

- Linting and syntax validation
- Image build and publish
- Deployment orchestration hooks

Workflow definitions are located in `.github/workflows/`.

The enterprise delivery pipeline is defined in `.github/workflows/enterprise-platform-delivery.yml` and validates tests, Kubernetes manifests, image builds, and staged deployment with `kubectl apply -k infrastructure/k8s`.
