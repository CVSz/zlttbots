# Project Structure

This repository is large enough that a structure map matters. The tree mixes runnable platform code, optional services, operational scripts, infrastructure assets, and blueprint modules.

## Top-level layout

```text
zlttbots/
├── AGENTS.md
├── CHANGELOG.md
├── LICENSE
├── README.md
├── configs/                        # Shared config such as nginx and env templates
├── contracts/                      # Service-level API/data contracts
├── docs/                           # Architecture, manuals, runbooks, setup, and reports
├── enterprise_maturity/            # Future-state / reference implementation modules
├── feature_repo/                   # Feature store definitions and feature metadata
├── infrastructure/                 # Monitoring, k8s, postgres, cloud, CI, bootstrap scripts
├── scripts/                        # Day-2 ops, install, deploy, repair, edge and node helpers
├── services/                       # Python and Node services / apps
├── tests/                          # Pytest validation for runtime and maturity modules
├── docker compose.yml              # Main local + extended platform compose definition
├── docker compose.enterprise.yml   # Additional enterprise deployment variant
├── start.sh                        # Fast bootstrap helper for Compose baseline
├── start-zttato.sh                 # Full bootstrap helper with node/python install flow
└── stop.sh                         # Stop helper
```

## 1) `services/`

The `services/` directory contains three broad categories.

### A. Baseline runtime services
These are the safest starting services and are used by the main gateway flow:

- `viral-predictor/`
- `market-crawler/`
- `arbitrage-engine/`
- `gpu-renderer/`

### B. Extended Compose/control-plane services
These expand platform automation and orchestration:

- `tenant-service/`
- `affiliate-webhook/`
- `execution-engine/`
- `product-generator/`
- `market-orchestrator/`
- `billing-service/`
- `landing-service/`
- `reward-collector/`
- `stream-consumer/`
- `feature-store/`
- `model-service/`
- `rl-engine/`, `rl-policy/`, `rl-coordinator/`, `rl-trainer/`
- `budget-allocator/`, `rtb-engine/`, `scaling-engine/`, `capital-allocator/`
- `model-registry/`, `model-sync/`, `drift-detector/`, `retraining-loop/`
- `federation/`, `scheduler/`, `p2p-node/`

### C. Standalone Node services / applications
These are typically run through Node tooling and PM2:

- `admin-panel/`
- `analytics/`
- `click-tracker/`
- `account-farm/`
- `ai-video-generator/`
- `shopee-crawler/`
- `tiktok-farm/`
- `tiktok-shop-miner/`
- `tiktok-uploader/`
- `edge-worker/`

### Typical contents of a service directory
Depending on the runtime, a service may contain:

- `Dockerfile`
- `docker/Dockerfile`
- `requirements.txt`
- `package.json`
- `src/` application code
- framework-level folders such as `app/`, `components/`, or `public`-style structures

## 2) `infrastructure/`

This directory holds deployment and environment assets beyond the main root Compose file.

### Major subareas
- `postgres/` — SQL migrations, PostgreSQL config, standalone database compose file
- `monitoring/` — Prometheus, Grafana, Loki, Promtail configs and compose file
- `k8s/` — Kubernetes manifests for deployments, services, ingress, monitoring, autoscaling, Kafka, JWT auth, mesh, and multi-region examples
- `cloudflare/` — Cloudflare/WAF/Tunnel-oriented infrastructure files
- `ci/` — build and deploy shell helpers
- `scripts/` — validation, bootstrap, cluster, rollback, optimization, and scan scripts
- `start/` — environment and worker helper scripts for host-side bootstrap flows

## 3) `scripts/`

Root-level `scripts/` is the operator toolbox. Main categories include:

- install and lifecycle helpers (`start-zttato`, node-service wrappers)
- cloud/edge provisioning and healing
- integration and doctor scripts
- repair, restart, and recovery scripts
- deployment automation

Frequently referenced scripts:

- `scripts/zttato-node.sh`
- `scripts/test-integration.sh`
- `scripts/start-zttato.sh`
- `scripts/stop-zttato.sh`
- `scripts/zttato-doctor.sh`
- `scripts/repair-platform.sh`
- `scripts/deploy-zttato-production.sh`

## 4) `docs/`

The docs tree is intentionally broad. It contains:

- platform overview and setup docs
- manuals by operator role
- architecture and service docs
- infrastructure docs
- runbooks and SLO/monitoring guidance
- development analyses and source scan reports
- API and database documentation
- UI/UX documentation

## 5) `enterprise_maturity/`

This area documents and implements advanced platform capabilities not always wired into baseline local startup. It includes modules for:

- governance
- performance
- resilience
- operations
- roadmap and upgrade logic
- v3 runtime capabilities such as service discovery, queue systems, autoscaling, crawler cluster, GPU scheduling, and API gateway behavior

## 6) `tests/`

The pytest suite validates multiple repository layers, not just one service. Examples include:

- auth behavior
- GPU renderer command generation
- model/runtime async patterns
- enterprise maturity modules
- advanced RL and distributed stack behavior
- safe-edge and production-maturity helpers

## 7) Files new contributors should know first

Start with these before making changes:

1. `README.md`
2. `docker compose.yml`
3. `configs/nginx.conf`
4. `docs/system-overview.md`
5. `docs/installation.md`
6. `docs/configuration.md`
7. the service directory you plan to modify

## 8) Active-by-default vs optional

### Active-by-default for the simplest local journey
- root Compose baseline services
- nginx gateway routes
- PostgreSQL migrations
- Redis-backed workers
- pytest-based repository validation

### Optional or environment-specific
- PM2-managed Node service fleet
- monitoring stack
- Kubernetes deployment path
- Cloudflare edge automation
- enterprise runtime patterns
- some extended Compose services that are defined for platform completeness but not routed publicly by default
