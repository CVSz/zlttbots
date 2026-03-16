# Enterprise Mesh, Event Bus, Security, and Delivery Stack

This repository now includes a production-style Kubernetes platform bundle under `infrastructure/k8s/` and `infrastructure/cloudflare/` that delivers:

- Service mesh with mTLS, JWT enforcement, and gateway routing.
- Kafka event bus with 3 broker replicas.
- Prometheus monitoring for mesh and service telemetry.
- GPU autoscaling with HPA and KEDA (Prometheus + Kafka lag triggers).
- JWT auth microservice for issuing and introspecting service tokens.
- Rate limiting at ingress (Nginx) and mesh gateway (Envoy local rate limiting).
- Cloudflare WAF rules managed through Terraform.

## Apply Kubernetes stack

```bash
kubectl apply -k infrastructure/k8s
```

## JWT auth service

Source: `services/jwt-auth`.

- `POST /token` issues JWT tokens.
- `GET /introspect` validates bearer token and returns claims.
- `GET /.well-known/jwks.json` exposes key metadata endpoint.

## Kafka

Source: `infrastructure/k8s/kafka/kafka.yaml`.

- Zookeeper + Kafka brokers exposed in-cluster at `kafka.platform.svc.cluster.local:9092`.

## Monitoring

Source: `infrastructure/k8s/monitoring/prometheus.yaml`.

- Prometheus service is exposed at `prometheus.platform.svc.cluster.local:9090`.
- Mesh proxy and Kubernetes service endpoint scraping are enabled.

## GPU autoscaling

Sources:

- `infrastructure/k8s/autoscale/gpu-renderer-hpa.yaml`
- `infrastructure/k8s/autoscale/gpu-renderer-keda.yaml`

GPU renderer scales from queue depth, Kafka lag, and GPU duty-cycle metrics.

## Cloudflare WAF

Terraform source:

- `infrastructure/cloudflare/waf-rules.tf`
- `infrastructure/cloudflare/variables.tf`

Apply:

```bash
cd infrastructure/cloudflare
terraform init
terraform apply
```
