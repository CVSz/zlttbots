# Project Structure

This repository contains a runnable platform, optional application services, deployment assets, and enterprise-scale reference code. Use this map to understand what is active by default and what is optional or environment-specific.

## Top-level layout

```text
zttato-platform/
├── configs/                    # Shared runtime configuration such as nginx routing
├── contracts/                  # Service API/data contracts
├── docs/                       # Overview docs, runbooks, manuals, architecture docs
├── enterprise_maturity/        # Enterprise blueprint and v3 runtime reference code
├── infrastructure/             # Monitoring, postgres, k8s, CI, scripts, cloud assets
├── scripts/                    # Operator helpers for install, deploy, repair, monitor, node lifecycle
├── services/                   # Python and Node services/apps
├── tests/                      # Pytest suite for runtime, GPU, auth, and maturity checks
├── docker-compose.yml          # Default local/runtime orchestration baseline
├── README.md                   # Repository entrypoint documentation
└── AGENTS.md                   # Repository-specific agent instructions
```

## 1) `services/`

The `services/` directory is the biggest part of the project. It contains both services used by the default Compose stack and additional applications used in other deployment modes.

### Services used by the default Compose stack
- `services/viral-predictor/` — FastAPI virality scoring service.
- `services/market-crawler/` — FastAPI crawler API plus worker.
- `services/arbitrage-engine/` — FastAPI arbitrage API plus worker.
- `services/gpu-renderer/` — FastAPI render queue API plus worker.

### Additional Python services
- `services/jwt-auth/` — JWT token issuer/introspection service.
- `services/ai-orchestrator/`
- `services/campaign-optimizer/`
- `services/product-discovery/`

### Additional Node.js services/apps
- `services/admin-panel/` — Next.js frontend.
- `services/analytics/`
- `services/click-tracker/`
- `services/account-farm/`
- `services/ai-video-generator/`
- `services/shopee-crawler/`
- `services/tiktok-farm/`
- `services/tiktok-shop-miner/`
- `services/tiktok-uploader/`

### Typical service contents
Depending on the service, you will see files such as:
- `Dockerfile`
- `docker/Dockerfile`
- `requirements.txt`
- `package.json`
- `src/` application code

## 2) `infrastructure/`

This directory contains environment and deployment assets that are broader than the local Compose file.

### Major subdirectories
- `infrastructure/postgres/` — standalone PostgreSQL compose file, config, and SQL migrations.
- `infrastructure/monitoring/` — Prometheus, Grafana, Loki, and Promtail stack.
- `infrastructure/k8s/` — Kubernetes namespace, deployments, services, ingress, autoscaling, Kafka, JWT auth, monitoring, and mesh configs.
- `infrastructure/cloudflare/` — Terraform-style Cloudflare config.
- `infrastructure/ci/` — build and deploy scripts.
- `infrastructure/scripts/` — validation, cluster bootstrap, rollout, rollback, and optimization helpers.
- `infrastructure/start/` — environment and worker startup helpers.

## 3) `scripts/`

Operational shell tooling lives here. Common categories include:
- stack startup/shutdown helpers
- node-service installation and PM2 lifecycle wrappers
- recovery and repair scripts
- Cloudflare/tunnel/deployment helpers
- monitoring and diagnostic commands

Frequently referenced scripts:
- `scripts/zttato-node.sh`
- `scripts/test-integration.sh`
- `scripts/start-zttato.sh`
- `scripts/stop-zttato.sh`
- `scripts/zttato-doctor.sh`
- `scripts/repair-platform.sh`

## 4) `docs/`

The docs tree contains:
- platform-level overview and setup docs
- manuals for user, admin, devops, and godmode personas
- architecture documents
- operational documentation
- API documentation folders

## 5) `enterprise_maturity/`

This area represents the broader platform direction beyond the default Compose baseline. Tests reference code here for features such as:
- service discovery
- API gateway routing
- central queueing
- backlog-based autoscaling
- distributed crawler management
- GPU scheduling

Treat this directory as a reference implementation and maturity blueprint rather than assuming every feature is part of the default local runtime.

## 6) `tests/`

The pytest suite currently covers multiple project layers:
- enterprise maturity and runtime behavior
- GPU renderer CPU/GPU command generation
- JWT auth token round-trip

This means the repository validates more than just the Compose stack; it also validates supporting platform capabilities and future-state modules.

## 7) Active-by-default vs optional

### Active by default
- `docker-compose.yml`
- `configs/nginx.conf`
- the four Python API services
- PostgreSQL and Redis
- the three worker processes

### Optional or environment-specific
- PM2-managed Node services
- monitoring stack
- Kubernetes assets
- Cloudflare automation
- JWT auth deployment
- enterprise maturity runtime modules

Knowing this split prevents confusion when reading the repository: not every directory is intended to start automatically in the baseline local environment.
