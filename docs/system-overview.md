# System Overview

zTTato Platform is a microservice-based affiliate automation system that combines product crawling, prediction, arbitrage scoring, rendering, and analytics workflows.

## 1) What the platform does

The platform is designed to support a full campaign lifecycle:

1. **Discover products** from external marketplaces.
2. **Score opportunities** using model-driven predictor services.
3. **Prioritize products/campaigns** through arbitrage logic.
4. **Render creative assets** with asynchronous worker execution.
5. **Track outcomes** and expose dashboards/metrics for optimization.

## 2) Runtime topology (Docker Compose baseline)

The default runtime in `docker-compose.yml` is composed of:

### Data services
- `postgres` (system-of-record relational data)
- `redis` (queueing/cache/state handoff for async workers)

### API and compute services
- `viral-predictor` (prediction API on internal port 9100)
- `market-crawler` (crawler API on internal port 9400)
- `arbitrage-engine` (arbitrage API on internal port 9500)
- `gpu-renderer` (renderer API on internal port 9300)

### Worker services
- `crawler-worker`
- `arbitrage-worker`
- `renderer-worker`

### Access/gateway
- `nginx` (exposes host `:80` and routes to internal APIs)

All services join the shared network `zttato-net` and rely on per-service health checks before dependency handoff.

## 3) Core data and request flow

A high-level operational flow:

1. Crawler service discovers product candidates and stores normalized records.
2. Predictor service evaluates candidates and emits opportunity scoring signals.
3. Arbitrage service combines score + economics to prioritize actions.
4. Worker pipelines run longer jobs (batch crawl, render, post-processing).
5. Output and behavior events feed analytics and admin-facing visibility.

## 4) Operational model

### Local and ops baseline
- Build: `docker compose build`
- Start: `docker compose up -d`
- Validate: `docker compose ps`
- Test: `pytest`

### Day-2 operations
- Logs: `docker compose logs --tail=200 <service>`
- Scale workers: `docker compose up -d --scale crawler-worker=3`
- Roll restart: `docker compose restart <service>`

## 5) Deployment and infrastructure options

The repository includes multiple deployment/operations paths:

- **Compose-first operations** for local, staging, and lightweight production setups.
- **Kubernetes assets** under `infrastructure/k8s/` for cluster-based deployments.
- **Cloudflare/devops automation** under `cloudflare-devops/` and `scripts/`.
- **Monitoring stack assets** in `infrastructure/monitoring/`.

## 6) Documentation map

For full-detail follow-up docs:

- Architecture and target model: `docs/architecture.md`, `docs/architecture-v3-enterprise.md`
- Installation and bootstrap: `docs/installation.md`, `docs/quick-start.md`
- API routes and contracts: `docs/api/`, `contracts/`
- Operations and runbooks: `docs/operations/`
- Role-based manuals: `docs/manuals/`
