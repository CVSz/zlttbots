# System Overview

zTTato Platform is a mixed Python and Node.js automation stack for social-commerce and affiliate operations. The repository includes a runnable Docker Compose baseline, optional PM2-managed Node services, monitoring assets, Kubernetes manifests, and an enterprise maturity blueprint used by the test suite.

## 1) What the platform does

At its core, the current runnable platform supports four main workflows:

1. **Product discovery** through the `market-crawler` API and its background worker.
2. **Virality scoring** through the `viral-predictor` API.
3. **Arbitrage analysis** through the `arbitrage-engine` API backed by PostgreSQL.
4. **Render queueing** through the `gpu-renderer` API and renderer worker, with CPU fallback available when GPU acceleration is not enabled.

The repository also contains additional services for admin, analytics, click tracking, TikTok automation, auth, video generation, and enterprise-scale runtime experiments, but those are not all enabled in the default Compose stack.

## 2) Runtime layers in this repository

### Compose baseline (`docker-compose.yml`)

The default local runtime is a 9-service stack:

#### Data layer
- `postgres` — primary relational database with schema bootstrap from `infrastructure/postgres/migrations/`.
- `redis` — queue and transient state backend for crawler and renderer workloads.

#### Python APIs
- `viral-predictor` — FastAPI service on container port `9100` for `/predict`, `/healthz`, and `/metrics`.
- `market-crawler` — FastAPI service on container port `9400` for `/crawl`, `/healthz`, and `/metrics`.
- `arbitrage-engine` — FastAPI service on container port `9500` for `/arbitrage`, `/healthz`, and `/metrics`.
- `gpu-renderer` — FastAPI service on container port `9300` for `/render`, `/healthz`, and `/metrics`.

#### Worker layer
- `crawler-worker` — processes queued crawl jobs.
- `arbitrage-worker` — background arbitrage worker process.
- `renderer-worker` — processes queued render jobs.

#### Access layer
- `nginx` — publishes host port `80`, returns a root health string at `/`, and proxies `/predict`, `/crawl`, and `/arbitrage` to their upstream services.

All Compose services run on the shared `zttato-net` bridge network and use Docker health checks for dependency ordering.

### Optional Node.js application layer

The `services/` directory also contains standalone Node.js services and applications that can be installed and run with `scripts/zttato-node.sh` and PM2. The current repository includes:

- `admin-panel` — Next.js admin frontend.
- `analytics` — Express + PostgreSQL service.
- `click-tracker` — tracking service with GeoIP support.
- `account-farm` — automation-oriented Node API.
- `ai-video-generator` — FFmpeg-assisted Node video pipeline.
- `shopee-crawler`, `tiktok-farm`, `tiktok-shop-miner`, `tiktok-uploader` — marketplace/social automation services.

These services are part of the broader project stack, but they are separate from the default Compose runtime.

### Infrastructure and enterprise assets

The repository also ships:

- **Monitoring compose assets** for Prometheus, Grafana, Loki, and Promtail under `infrastructure/monitoring/`.
- **Kubernetes manifests** under `infrastructure/k8s/` for deployments, ingress, autoscaling, JWT auth, Kafka, service mesh, and monitoring integration.
- **Cloudflare and deployment automation** under `scripts/`, `infrastructure/scripts/`, and `infrastructure/cloudflare/`.
- **Enterprise runtime reference code and tests** under `enterprise_maturity/` and `tests/`, covering API gateway routing, service discovery, autoscaling, queueing, distributed crawler behavior, and GPU scheduling.

## 3) Request and data flow

### Compose baseline flow

1. A client calls Nginx on `http://localhost`.
2. Nginx routes:
   - `/predict` -> `viral-predictor`
   - `/crawl` -> `market-crawler`
   - `/arbitrage` -> `arbitrage-engine`
3. `market-crawler` pushes crawl jobs into Redis for `crawler-worker`.
4. `gpu-renderer` pushes render jobs into Redis for `renderer-worker`.
5. `viral-predictor` and `arbitrage-engine` use PostgreSQL-backed data and metrics.
6. PostgreSQL stores products, campaigns, videos, jobs, arbitrage events, clicks, and orders.

### Data model highlights

The bootstrap schema creates these major tables:

- `accounts`, `proxies`
- `products`, `tiktok_products`
- `campaigns`, `videos`, `jobs`
- `clicks`, `orders`
- `arbitrage_events`

That schema shows the platform is designed around a commerce funnel: discovery -> campaign creation -> media/job execution -> click/order tracking -> arbitrage and optimization.

## 4) Public and internal interfaces

### Public host entrypoints
- `http://localhost/` — Nginx health string.
- `http://localhost/predict` — proxied predictor endpoint.
- `http://localhost/crawl` — proxied crawler endpoint.
- `http://localhost/arbitrage` — proxied arbitrage endpoint.

### Direct internal service ports
- Predictor: `9100`
- Renderer: `9300`
- Crawler: `9400`
- Arbitrage: `9500`
- Postgres: `5432` internally in Compose
- Redis: `6379` internally in Compose

### Additional service interfaces in the repo
- `jwt-auth` exposes `/healthz`, `/.well-known/jwks.json`, `/token`, and `/introspect` for token issuance and verification when deployed separately.
- Node services expose their own application servers when started via PM2 or other deployment paths.

## 5) Operational model

### Baseline local lifecycle
- Build: `docker compose build`
- Start: `docker compose up -d`
- Inspect: `docker compose ps`
- Logs: `docker compose logs --tail=200 <service>`
- Test: `pytest`

### Optional Node service lifecycle
- Install dependencies: `bash scripts/zttato-node.sh install`
- Start PM2-managed services: `bash scripts/zttato-node.sh start`
- Inspect PM2 processes: `bash scripts/zttato-node.sh status`
- View logs: `bash scripts/zttato-node.sh logs [service]`

### Monitoring lifecycle
- Start monitoring stack: `docker compose -f infrastructure/monitoring/docker-compose.monitoring.yml up -d`
- Access Prometheus on `:9090`, Grafana on `:3000`, and Loki on `:3100`.

## 6) Architecture boundaries to keep in mind

This repository has three distinct layers of scope:

1. **Runnable default platform** — the Compose stack most operators will use first.
2. **Extended service inventory** — additional Node and Python services included in `services/` and K8s manifests.
3. **Enterprise maturity blueprint** — higher-scale patterns represented in code and tests, including service discovery, queue orchestration, auto-scaling, and GPU scheduling.

When updating or operating the platform, be explicit about which layer you mean so documentation, tests, and deployment steps stay aligned.
