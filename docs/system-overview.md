# System Overview

zTTato Platform is a mixed Python, Node.js, shell, Docker, and infrastructure-code repository for social-commerce automation, affiliate workflow execution, analytics, and operator tooling. The project is not just one app: it is a platform with a safe baseline runtime, a broader orchestration stack, optional Node-managed applications, and enterprise-scale reference modules.

## 1) Platform modes

### A. Baseline local runtime
The safest starting point is the baseline Compose environment used for local validation and smoke checks. Its primary business flows are:

1. **Virality scoring** via `viral-predictor`.
2. **Product discovery queueing** via `market-crawler` and `crawler-worker`.
3. **Arbitrage review** via `arbitrage-engine` and `arbitrage-worker`.
4. **Render queue intake** via `gpu-renderer` and `renderer-worker`.
5. **Gateway access** via `nginx`.
6. **Stateful storage** via PostgreSQL and Redis.

### B. Expanded Compose control plane
The same `docker-compose.yml` also declares a larger product/launch/reward/ML control plane. This extends the platform with:

- tenant onboarding and API key issuance
- affiliate conversion ingestion
- publishing/execution bridge calls to a partner API
- product, market, billing, and landing-generation workflows
- reward event streaming with Redpanda/Kafka-like messaging
- feature-store, model-serving, registry, sync, retraining, and drift-detection services
- RL training, coordination, policy, budget, scaling, and orchestration services
- Ray-based distributed compute building blocks

### C. Standalone Node application layer
A separate operator path exists for Node applications under `services/`, especially:

- `admin-panel`
- `analytics`
- `click-tracker`
- `account-farm`
- `ai-video-generator`
- `shopee-crawler`
- `tiktok-farm`
- `tiktok-shop-miner`
- `tiktok-uploader`

These are typically installed and run with `scripts/zttato-node.sh` and PM2 rather than through the baseline Compose gateway.

### D. Enterprise blueprint layer
The `enterprise_maturity/` tree and `tests/` capture future-state and alternate deployment patterns such as:

- service discovery
- API gateway routing
- queue orchestration
- autoscaling logic
- distributed crawler coordination
- GPU scheduling
- resilience and governance controls

## 2) Current Compose topology

### Data layer
- `postgres` — primary relational store with schema bootstrap from `infrastructure/postgres/migrations/`.
- `redis` — transient queue/state backend for crawler, renderer, and other runtime helpers.
- `redpanda` — event-stream backbone for reward, feature, and RL-oriented workflows.

### Baseline API layer
- `viral-predictor` — FastAPI on port `9100` inside the network.
- `market-crawler` — FastAPI on port `9400`.
- `arbitrage-engine` — FastAPI on port `9500`.
- `gpu-renderer` — FastAPI on port `9300`.

### Worker layer
- `crawler-worker`
- `arbitrage-worker`
- `renderer-worker`
- additional data/ML workers in the extended stack such as `stream-consumer`, `rl-trainer`, `model-sync`, and `retraining-loop`

### Business/control-plane APIs
- `tenant-service` — tenant creation and API key issuance on port `8000`
- `affiliate-webhook` — verified conversion ingestion on port `9700`
- `execution-engine` — partner publish/status bridge on port `9600`
- `product-generator`, `market-orchestrator`, `billing-service`, `landing-service`, `reward-collector`, `feature-store`, `model-service`, `rl-engine`, `budget-allocator`, `rtb-engine`, `scaling-engine`, `master-orchestrator`, `federation`, `scheduler`, `capital-allocator`, `model-registry`, `rl-policy`, and related services mostly on internal port `8000`

### Edge layer
- `nginx` exposes port `80` on the host and currently proxies only `/`, `/predict`, `/crawl`, and `/arbitrage`.

## 3) Current request/data flow

### Baseline flow
1. Client calls `http://localhost`.
2. Nginx routes supported paths to predictor, crawler, or arbitrage services.
3. Crawler and renderer services enqueue work into Redis.
4. Workers consume background jobs from Redis.
5. Predictor and arbitrage services interact with PostgreSQL-backed data.
6. PostgreSQL stores products, videos, campaigns, clicks, orders, arbitrage events, tenants, and related operational data.

### Extended flow examples
- `tenant-service` provisions tenant records and API keys.
- `affiliate-webhook` verifies a signed callback, records conversion metrics, and forwards normalized reward data to `reward-collector`.
- `execution-engine` rate-limits and forwards publish/status requests to an external partner API.
- `master-orchestrator` depends on multiple optimization and ML services to coordinate broader AI economy workflows.

## 4) Public vs internal interfaces

### Public host entrypoints today
- `GET http://localhost/`
- `POST http://localhost/predict`
- `POST http://localhost/crawl`
- `GET http://localhost/arbitrage`
- `GET http://localhost:8265` for Ray dashboard when the distributed runtime is started

### Internal-only interfaces by default
Most extended Compose services have no host-port mapping. They are intended for:

- internal Compose-to-Compose communication
- later ingress exposure through nginx, Cloudflare, or Kubernetes
- local debugging by `docker compose exec` or temporary port-forward changes

## 5) Database and queue shape

The bootstrap schema under `infrastructure/postgres/migrations/` indicates a commerce and operations domain centered around:

- accounts and proxies
- products and TikTok products
- campaigns and videos
- jobs and execution records
- clicks and orders
- arbitrage events
- tenants and campaign metrics

This signals a platform design that spans discovery, enrichment, media operations, monetization, optimization, and operator review.

## 6) Operational boundaries to keep in mind

### Baseline-first rule
For setup, smoke checks, incident triage, and onboarding, start with the baseline runtime. It is the narrowest and most predictable path.

### Extended-runtime caution
The broader Compose file contains services that are present and buildable, but not all are fully surfaced through public routes or documented for first-day use. Treat them as internal platform components unless your environment explicitly enables them.

### Node-service separation
The Node service fleet is real and part of the repository, but it follows a different runtime path from the baseline nginx gateway.

### Enterprise blueprint distinction
The test suite validates broader design patterns than the day-one local runtime. Keep documentation explicit about what is live by default versus what is reference architecture.
