# zTTato Feature Impact Dive

- Generated from repository sources on 2026-04-06 (UTC).
- Compose services discovered: **43**
- Node app features discovered: **7**
- Runtime service modules discovered: **46**
- Service documentation feature specs: **11**
- Aggregate discovered feature surfaces: **107**

## Compose Service Surface

- affiliate-webhook
- arbitrage-engine
- arbitrage-worker
- billing-service
- budget-allocator
- capital-allocator
- crawler-worker
- drift-detector
- execution-engine
- feature-store
- federation
- gpu-renderer
- landing-service
- market-crawler
- market-orchestrator
- master-orchestrator
- model-registry
- model-service
- model-sync
- nginx
- p2p-node
- payment-gateway
- postgres
- product-generator
- ray-head
- ray-worker
- redis
- redpanda
- renderer-worker
- retraining-loop
- reward-collector
- rl-agent-1
- rl-agent-2
- rl-coordinator
- rl-engine
- rl-policy
- rl-trainer
- rtb-engine
- scaling-engine
- scheduler
- stream-consumer
- tenant-service
- viral-predictor

## Application API Surface

- api-gateway (1 endpoints): GET /healthz
- auth-service (3 endpoints): GET /healthz, POST /login, POST /register
- billing-service (4 endpoints): GET /healthz, GET /plan/:userId, POST /checkout, POST /webhook
- frontend (0 endpoints): no HTTP routes found
- log-service (2 endpoints): GET /healthz, POST /log
- platform-core (7 endpoints): GET /github/repos, GET /healthz, GET /projects/public, POST /deploy, POST /deploy/github, POST /orgs, POST /orgs/:orgId/members
- worker-ai (2 endpoints): GET /healthz, POST /fix

## Runtime Service API Surface

- account-farm [node] (2 endpoints): GET /farm/health, POST /farm/run
- affiliate-webhook [python] (2 endpoints): GET /healthz, POST /conversion
- ai-orchestrator [python] (2 endpoints): GET /health, POST /run-growth-cycle
- ai-video-generator [node] (0 endpoints): no HTTP routes found
- analytics [node] (6 endpoints): GET /analytics/campaigns, GET /analytics/conversion, GET /analytics/products, GET /analytics/revenue, GET /analytics/summary, GET /healthz
- arbitrage-engine [python] (11 endpoints): GET /arbitrage, GET /healthz, GET /metrics, GET /publishing/counters/{tenant_id}, GET /reporting/posted-products/{tenant_id}, POST /affiliate/payouts/ingest, POST /affiliate/sync, POST /performance, POST /publishing/jobs, POST /publishing/run-daily, POST /videos
- billing-service [python] (2 endpoints): GET /healthz, POST /charge
- budget-allocator [python] (2 endpoints): GET /healthz, POST /allocate
- campaign-optimizer [python] (1 endpoints): POST /optimize
- capital-allocator [python] (2 endpoints): GET /healthz, POST /allocate
- click-tracker [node] (0 endpoints): no HTTP routes found
- creative-generator [python] (0 endpoints): no HTTP routes found
- drift-detector [python] (0 endpoints): no HTTP routes found
- exchange [python] (1 endpoints): POST /order
- execution-engine [python] (3 endpoints): GET /healthz, GET /status/{external_id}, POST /publish
- feature-store [python] (5 endpoints): GET /features/{campaign_id}, GET /healthz, POST /features/{campaign_id}, PUT /features, PUT /features/{campaign_id}
- federation [python] (3 endpoints): GET /healthz, GET /nodes, POST /register
- gpu-renderer [python] (3 endpoints): GET /healthz, GET /metrics, POST /render
- jwt-auth [python] (4 endpoints): GET /.well-known/jwks.json, GET /healthz, GET /introspect, POST /token
- landing-service [python] (2 endpoints): GET /healthz, GET /landing/{product_id}
- market-crawler [python] (3 endpoints): GET /healthz, GET /metrics, POST /crawl
- market-orchestrator [python] (2 endpoints): GET /healthz, POST /launch
- master-orchestrator [python] (9 endpoints): GET /deployments/{deployment_id}, GET /healthz, POST /campaign/run, POST /deployments, POST /deployments/events, POST /economy/run, POST /federation/run, POST /profit-mode/activate, POST /run-cycle
- model-registry [python] (3 endpoints): GET /healthz, GET /latest/{name}, POST /register
- model-service [python] (6 endpoints): GET /healthz, GET /metrics, GET /result/{job_id}, GET /result/{job_id}/wait, POST /predict, POST /predict_async
- model-sync [python] (0 endpoints): no HTTP routes found
- network-egress [python] (0 endpoints): no HTTP routes found
- p2p-node [node] (0 endpoints): no HTTP routes found
- product-discovery [python] (2 endpoints): GET /discover, GET /healthz
- product-generator [python] (2 endpoints): GET /healthz, POST /generate
- retraining-loop [python] (0 endpoints): no HTTP routes found
- reward-collector [python] (2 endpoints): GET /healthz, POST /reward
- rl-coordinator [python] (3 endpoints): GET /healthz, POST /decide, POST /update
- rl-engine [python] (3 endpoints): GET /healthz, POST /select, POST /update
- rl-policy [python] (2 endpoints): GET /healthz, POST /train
- rl-trainer [python] (0 endpoints): no HTTP routes found
- rtb-engine [python] (3 endpoints): GET /healthz, POST /bid, POST /openrtb/bid
- scaling-engine [python] (2 endpoints): GET /healthz, POST /scale
- scheduler [python] (2 endpoints): GET /healthz, POST /assign
- shopee-crawler [node] (0 endpoints): no HTTP routes found
- stream-consumer [python] (0 endpoints): no HTTP routes found
- tenant-service [python] (2 endpoints): GET /healthz, POST /tenant
- tiktok-farm [node] (2 endpoints): GET /farm/status, POST /farm/job
- tiktok-shop-miner [node] (0 endpoints): no HTTP routes found
- tiktok-uploader [node] (0 endpoints): no HTTP routes found
- viral-predictor [python] (3 endpoints): GET /healthz, GET /metrics, POST /predict

## Documented Product Feature Surface

- account-farm: Account Farm Service
- admin-panel: Admin Panel
- ai-video-generator: AI Video Generator Service
- analytics: Analytics Service
- arbitrage-engine: Arbitrage Engine Service
- click-tracker: Click Tracker Service
- gpu-renderer: GPU Renderer Service
- market-crawler: Market Crawler Service
- master-orchestrator: Master Orchestrator Service
- tiktok-uploader: TikTok Uploader Service
- viral-predictor: Viral Predictor Service

## Recommended Fixes

1. Consolidate duplicated feature naming between compose services, runtime services, and docs/services into a single source-of-truth manifest.
2. Add this script to CI to detect undocumented apps, runtime modules, or routes drift.
3. Review all write endpoints and enforce tenant/auth middleware and schema validation at service level.
