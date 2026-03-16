# System Architecture

This document describes the current service architecture and execution flow for zTTato Platform.

## 1) Architectural style

The platform follows a **microservice + async worker** pattern:

- Thin API services expose business capabilities.
- Data and queue infrastructure are centralized via Postgres and Redis.
- Worker processes execute long-running tasks decoupled from request/response APIs.
- Nginx provides a single ingress endpoint for core API routes.

## 2) Layered architecture

### Layer A: Ingestion
- `market-crawler`
- `crawler-worker`

Purpose: discover, normalize, and queue product intelligence.

### Layer B: Intelligence and scoring
- `viral-predictor`
- `arbitrage-engine`
- `arbitrage-worker`

Purpose: generate predictions and convert them into prioritized business actions.

### Layer C: Asset generation
- `gpu-renderer`
- `renderer-worker`

Purpose: process media/render workloads and asynchronous creative pipelines.

### Layer D: Access and control
- `nginx` API gateway
- `admin-panel` (project UI app in repository, commonly run in frontend workflows)

Purpose: route users/operators to service capabilities and visibility tooling.

### Layer E: Persistence and queueing
- `postgres`
- `redis`

Purpose: durable storage + task coordination.

## 3) Request path and asynchronous flow

### Synchronous path (API gateway)
1. Client sends request to `http://localhost/<route>`.
2. Nginx forwards to mapped internal service (`/predict`, `/crawl`, `/arbitrage`).
3. Service validates input, performs fast-path processing, and persists/returns response.

### Asynchronous path (worker-based)
1. API service stores task metadata and/or enqueues work in Redis-backed flow.
2. Worker picks job and performs compute-intensive or long-running execution.
3. Worker writes results to Postgres and exposes status through APIs/analytics surfaces.

## 4) Reliability and health model

- Compose defines per-service health checks for startup dependency gating.
- `depends_on` with `service_healthy` enforces startup ordering for critical dependencies.
- Worker scaling is horizontal by replica count (`docker compose up -d --scale ...`).
- Logs + endpoint probes provide first-line incident diagnostics.

## 5) Security and control boundaries

- Service communication is isolated on the internal `zttato-net` bridge network.
- External exposure is minimized to nginx (`:80`) unless explicitly configured.
- Secrets are expected through `.env` and runtime environment injection.
- Additional enterprise hardening artifacts are available in infra/security docs.

## 6) Evolution path

Current architecture is a compose-centered baseline. The enterprise target model (service mesh, autoscaling, governance, SLO-backed operations) is documented in:

- `docs/architecture-v3-enterprise.md`
- `docs/operations/enterprise-production-maturity-roadmap.md`
- `docs/operations/enterprise-production-maturity-implementation.md`
