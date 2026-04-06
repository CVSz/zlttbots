# zTTato Platform Full Feature Deep Dive

**Date (UTC):** 2026-04-06  
**Scope:** Whole repository feature topology and runtime capability mapping

## 1) Platform shape at a glance

- **Monorepo with multiple execution planes:**
  - `apps/` for core product-facing gateway/auth/platform services and frontend.
  - `services/` for specialized domain microservices (AI, data, orchestration, commerce, tracking, rendering, RL, model lifecycle).
  - `enterprise_maturity/` for blueprint-grade platform modules (governance, resilience, security, autoscaling, discovery).
  - `infra/`, `infrastructure/`, `installer/`, and `scripts/` for deployment, operations, and bootstrapping.
- **Current Compose runtime defines 43 services**, including stateful infra (`postgres`, `redis`, `redpanda`), orchestration (`ray-head`, `ray-worker`), and feature services (affiliate, model, RL, billing, scaling, rendering).

## 2) Feature inventory by domain

## A. Identity, tenancy, and access

- `apps/auth-service`: authentication and account registration with secure password hashing workflows.
- `services/jwt-auth`: token validation/signing helper service pattern.
- `services/tenant-service`: tenant-centric operational domain.
- `services/identity` and `services/org`: identity/org boundaries for multi-tenant expansion.

## B. API edge and platform control plane

- `apps/api-gateway`: edge ingress, policy enforcement, and request routing.
- `apps/platform-core`: core control-plane endpoints and deployment workflow integration.
- `apps/log-service`: centralized operational logging API.
- `services/master-orchestrator`: higher-order orchestration and service coordination.

## C. Commerce, payments, and affiliate workflows

- `apps/billing-service` and `services/billing-service`: billing and subscription operation surfaces.
- `services/payment` + `payment-gateway` compose role: payment rails and webhook/event settlement pattern.
- `services/affiliate-webhook`: partner conversion/event intake.
- `services/arbitrage-engine`, `services/capital-allocator`, `services/budget-allocator`: decisioning around spend/profit loops.

## D. AI/ML lifecycle and inference mesh

- `services/model-service`, `services/model-sync`, `services/model-registry`: model lifecycle and synchronization responsibilities.
- `services/feature-store`: feature persistence and retrieval.
- `services/auto-ml`, `services/retraining-loop`, `services/drift-detector`, `services/self-modifier`: continuous learning and adaptation path.
- `services/ai-orchestrator`, `services/execution-engine`: AI task execution and routing.

## E. Reinforcement-learning stack

- `services/rl-engine`, `services/rl-policy`, `services/rl-trainer`, `services/rl-coordinator`.
- Compose includes dedicated RL replicas (`rl-agent-1`, `rl-agent-2`) for distributed experimentation/execution.

## F. Acquisition, growth, and market intelligence

- `services/product-discovery`, `services/product-generator`, `services/market-crawler`, `services/market-orchestrator`.
- `services/viral-predictor`, `services/campaign-optimizer`, `services/tracking`, `services/click-tracker`.
- Social channel automation surfaces: `services/tiktok-farm`, `services/tiktok-uploader`, `services/tiktok-shop-miner`, `services/shopee-crawler`.

## G. Rendering and compute substrate

- `services/gpu-renderer`, `services/ai-video-generator`, `services/gpu`.
- Distributed execution primitives in Compose via Ray (`ray-head`, `ray-worker`) and worker services (`crawler-worker`, `renderer-worker`, `arbitrage-worker`).

## H. Reliability, operations, and enterprise controls

- `enterprise_maturity/` modules include:
  - Resilience controls (retry, idempotency, circuit breaker).
  - Security controls (RBAC, audit pipeline, secret rotation policy).
  - Operations/SLO modules and governance/versioning helpers.
  - v3 runtime references (autoscaling, queue systems, service discovery).
- `tests/` validates these patterns with broad integration-style and component tests.

## 3) Fix generated from this deep dive

### Target

- `services/network-egress/src/client.py`

### Problem observed

- Request exception path used silent `pass`, reducing diagnosability and violating security/operational audit expectations.
- No URL guardrails against unsafe target classes (e.g., private/loopback IPs), creating SSRF exposure risk if misused upstream.
- Missing deterministic input validation on timeout/retry/backoff.

### Implemented hardening

- Added strict constructor validation (`timeout`, `retries`, `backoff`).
- Added URL validation:
  - `http/https` only.
  - hostname required.
  - optional host allowlist support.
  - private/loopback/link-local IP target blocking.
- Replaced silent exception handling with structured warning logs and retained last failure context.
- Added deterministic retry loop with exponential backoff and explicit error reporting.

### Regression coverage

- Added `tests/test_network_egress_client.py` to verify:
  - retry-then-success behavior,
  - retry exhaustion failure path,
  - allowlist enforcement,
  - private address rejection.
