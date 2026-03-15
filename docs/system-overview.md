# System Overview

zTTato Platform is an AI-assisted affiliate automation system for product discovery, campaign acceleration, and conversion optimization.

## Platform objectives

- Discover profitable products from marketplaces.
- Score opportunities using ML/prediction services.
- Automate campaign publishing workflows.
- Track click/conversion performance and optimize outcomes.

## High-level architecture

### Data layer

- `postgres`: persistent relational storage
- `redis`: queue/cache and worker coordination

### API and compute services

- `viral-predictor`
- `market-crawler`
- `arbitrage-engine`
- `gpu-renderer`
- analytics/click-tracking services

### Worker layer

- `crawler-worker`
- `renderer-worker`
- `arbitrage-worker`

### Access layer

- `nginx`: reverse-proxy and route gateway
- `admin-panel`: web UI for operators/admins

## Core request and processing flow

1. Ingestion/crawl discovers product candidates.
2. Predictor and analytics services score opportunities.
3. Workers process long-running jobs asynchronously.
4. Dashboard and API consumers observe results and operate campaigns.

## Operations model

- Container orchestration: Docker Compose (local/ops baseline)
- Optional deployment manifests: Kubernetes assets in `infrastructure/k8s/`
- Operational automation: shell scripts in `scripts/` and `infrastructure/scripts/`
