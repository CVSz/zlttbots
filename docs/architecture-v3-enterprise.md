# zlttbots v3 Enterprise Upgrade Design

This document defines the v3 Enterprise target architecture and migration path for the current v2 production stack.

## 1) Current State (v2)

### Runtime service groups

- **Node automation services**: `shopee-crawler`, `tiktok-farm`, `analytics`, `ai-video-generator`, `click-tracker`, `account-farm`
- **Python compute services**: `market-crawler`, `viral-predictor`, `arbitrage-engine`, `gpu-renderer`
- **Workers**: `crawler-worker`, `renderer-worker`, `arbitrage-worker`
- **Infrastructure**: PostgreSQL, Redis, NGINX, Cloudflare tunnel

### Strengths

- Microservice-based decomposition
- Queue worker execution model
- AI inference + rendering capabilities
- Containerized deployment path

### Main gaps to solve in v3

- No dynamic service discovery for routing
- Queue architecture is Redis-centric and limited for event-stream scale
- Limited observability in traces/logs/metrics correlation
- Automation orchestration is fragmented across services

## 2) Target Architecture (v3 Enterprise)

```text
                    Cloudflare Edge
                          |
                    API Gateway
                      (Traefik)
                          |
        +-----------------+-----------------+
        |                 |                 |
   Automation API    Analytics API    Admin API
        |                 |                 |
 +------+-------+   +-----+-----+   +-------+-------+
 | TikTok Farm  |   | ClickTrack|   | Dashboard UI |
 | Account Farm |   | Campaigns |   | Admin Panel  |
 | Shopee Miner |   | Orders    |   | Billing      |
 +------+-------+   +-----+-----+   +---------------+
        |
        v
     Event Bus (Kafka)
        |
 +------+-------------------+
 |                          |
Crawler Cluster         AI Pipeline
 |                       |
 v                       v
market crawler       viral predictor
price scanner        gpu renderer
arbitrage AI         video generator

Storage:
PostgreSQL | Redis | S3 Object Storage | ClickHouse
```

## 3) Major upgrade domains

### A. API Gateway modernization

Replace NGINX edge routing with Traefik to support:

- Dynamic service discovery
- Automatic TLS lifecycle
- Route-level rate limiting
- Auth middleware chaining (JWT/OIDC forward auth)

### B. Event backbone evolution

Retain Redis for cache/ephemeral queue use, but move inter-service domain events to Kafka.

**Initial topics**:

- `crawl.jobs`
- `video.render`
- `tiktok.upload`
- `analytics.events`

### C. AI pipeline split

Break current AI/video services into composable pipeline stages:

1. Script generator
2. Voice generator
3. Video renderer
4. Upload automation

### D. Distributed crawler fleet

Standardize crawler contracts and scale horizontally by crawler type:

- Amazon crawler
- TikTok Shop crawler
- Shopee crawler
- Lazada crawler

Target: 100+ crawler workers with autoscaling policies.

## 4) Proposed repository layout (v3)

```text
zlttbots-v3
|
+- gateway/
|  +- traefik/
|
+- services/
|  +- automation/
|  |  +- tiktok-farm/
|  |  +- account-farm/
|  |  +- uploader/
|  +- analytics/
|  |  +- click-tracker/
|  |  +- campaign-engine/
|  +- admin/
|     +- dashboard/
|
+- ai/
|  +- video-pipeline/
|  +- viral-predictor/
|  +- arbitrage-ai/
|
+- crawlers/
|  +- shopee/
|  +- tiktok/
|  +- amazon/
|  +- lazada/
|
+- workers/
|  +- crawler-workers/
|  +- render-workers/
|  +- automation-workers/
|
+- infrastructure/
|  +- postgres/
|  +- redis/
|  +- kafka/
|  +- monitoring/
|  +- scripts/
|
+- deploy/
   +- docker/
   +- kubernetes/
```

## 5) Observability baseline (required)

Adopt full stack observability:

- **Prometheus** for metrics
- **Grafana** for dashboards
- **Loki** for logs
- **Jaeger** for tracing

Core SLI/SLO metric families:

- Crawler throughput
- AI inference/render latency
- API error ratio and p95/p99 latency
- Worker queue depth and event lag

## 6) Security upgrades

Minimum enterprise controls:

- JWT authentication and scoped authorization
- API-level rate limiting and abuse protection
- Service-to-service security posture (service mesh ready, e.g. Istio)
- Secret lifecycle management with a secrets manager

## 7) Deployment model: compose to Kubernetes

Primary runtime target should be Kubernetes:

- Crawler pods
- AI pipeline pods
- API pods
- Worker pods

Autoscaling requirements:

- HPA for stateless services
- Dedicated GPU node pool for rendering/inference stages

## 8) CI/CD blueprint

GitHub Actions stages:

1. Build
2. Test
3. Container image build
4. Push to registry
5. Deploy to Kubernetes

## 9) Automation orchestration layer

Add `n8n` as workflow orchestration for cross-service lifecycle automation:

1. Crawl product
2. Detect trend
3. Generate video
4. Upload to TikTok
5. Track analytics

## 10) Migration plan (phased)

### Phase 1: Platform foundation

- Introduce Traefik in parallel with existing NGINX
- Stand up Kafka cluster and start dual-publish from critical producers
- Add Prometheus + Grafana + Loki + Jaeger baseline

### Phase 2: Service refactor and contracts

- Split AI pipeline into independent services with explicit contracts
- Normalize crawler service interfaces and worker protocol
- Add shared API auth middleware and tenant/account boundaries

### Phase 3: Kubernetes and scaling

- Move all APIs/workers to Kubernetes deployment manifests/Helm
- Enable HPA and GPU node pools
- Move analytics workloads to ClickHouse-backed storage paths where needed

### Phase 4: Orchestration and enterprise operations

- Add n8n workflow templates and operational runbooks
- Add canary/blue-green deployment strategies
- Define production SLOs, on-call alerts, and disaster recovery drills

## 11) Final capability profile (v3)

With this upgrade, the platform evolves from **zlttbots v2 production** to **zlttbots v3 enterprise**, enabling:

- Automatic TikTok video generation at scale
- Account farming and upload automation workflows
- Distributed product crawling across multiple marketplaces
- AI-assisted trend and arbitrage detection
- Campaign automation and analytics feedback loops
