# zTTato Feature Impact Dive

- Generated from repository sources on 2026-04-06 (UTC).
- Compose services discovered: **43**
- Node app features discovered: **6**
- Service documentation feature specs: **11**
- Aggregate discovered feature surfaces: **60**

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

- api-gateway (1 endpoints): /healthz
- auth-service (3 endpoints): /healthz, /login, /register
- billing-service (4 endpoints): /checkout, /healthz, /plan/:userId, /webhook
- log-service (2 endpoints): /healthz, /log
- platform-core (7 endpoints): /deploy, /deploy/github, /github/repos, /healthz, /orgs, /orgs/:orgId/members, /projects/public
- worker-ai (2 endpoints): /fix, /healthz

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

1. Consolidate duplicated feature naming between compose services and docs/services into a single source-of-truth manifest.
2. Add this script to CI to detect undocumented apps or routes drift.
3. Review app routes that expose write endpoints and enforce tenant/auth middleware at service level.
