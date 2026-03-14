# Repository Analysis (2026-03-14)

This document captures a practical technical analysis of the current `zttato-platform` repository state, with emphasis on architecture shape, engineering maturity, and operational risks.

## 1) High-level architecture

The repository is organized as a microservice platform with:

- **Python compute services** (for prediction, crawling, arbitrage, rendering).
- **Node.js product/services layer** (analytics, tracking, upload automation, admin panel).
- **Shared infra primitives**: PostgreSQL + Redis.
- **Ingress layer**: NGINX reverse proxy.
- **Container-first orchestration**: Docker Compose locally and Kubernetes manifests in `infrastructure/k8s`.

The root Compose stack currently defines `postgres`, `redis`, three Python API services, one renderer service, three workers, and `nginx`, with health checks and dependency ordering already enabled.

## 2) Codebase composition and structure signals

A quick static inventory indicates a mixed-technology codebase:

- JavaScript/JSX files dominate service-level API/UI logic.
- Python files power compute and worker subsystems.
- Shell scripts are heavily used for bootstrap, diagnostics, and operational workflows.
- Documentation coverage is strong and spread across development, operations, infrastructure, and API folders.

This structure is good for separation of concerns, but it also implies the need for **multi-runtime CI discipline** and explicit ownership boundaries by service.

## 3) Operational readiness observations

### What is already strong

1. **Compose health model exists**  
   Critical services have health checks and dependency conditions wired in Compose, improving startup determinism.

2. **Worker separation is explicit**  
   Dedicated worker containers (`crawler-worker`, `arbitrage-worker`, `renderer-worker`) reflect an asynchronous processing model that can scale independently.

3. **Repo-level validation script exists**  
   `infrastructure/scripts/validate-repo.sh` provides basic syntax and manifest sanity checks across shell, Python, and `package.json` files.

4. **Operational documentation is present**  
   The repository includes playbook-like docs and environment guidance, reducing onboarding friction.

### Gaps and risks

1. **CI pipeline scope is incomplete relative to deployed stack**  
   The current GitHub Actions workflow builds/pushes only selected Node services and deploys Kubernetes manifests, but does not appear to run test/lint gates or build all Python/runtime components represented in Compose.

2. **Push-only main-branch trigger**  
   Workflow triggers only on `push` to `main`, which weakens pull-request feedback loops and can delay defect detection.

3. **No explicit contract-testing layer in CI**  
   Given cross-service communication and worker pipelines, the absence of strongly enforced contract checks increases integration drift risk.

4. **Potential config drift between Compose and K8s**  
   Dual orchestration modes exist; without parity checks, probes/env/resources can diverge over time.

## 4) Architecture and delivery recommendations

### Immediate (1–2 weeks)

- Add a PR-triggered CI workflow (or expand existing one) with at minimum:
  - Shell/Python/JSON validation
  - Per-service lint/test jobs
  - Integration smoke test stage
- Add a build matrix for Python services and workers currently absent from image build/push steps.
- Introduce a mandatory status-check policy for merge.

### Near-term (2–4 weeks)

- Add API/queue contract tests for highest-risk service boundaries.
- Enforce structured logging schema (`service`, `request_id`, `trace_id`, `latency_ms`, `status`) across Python and Node services.
- Add compose-vs-k8s parity validation for health probes and required environment keys.

### Medium-term (4–8 weeks)

- Formalize service ownership map and on-call rotations.
- Add SLO dashboard definitions and incident runbooks tied to top failure modes.
- Add supply-chain scanning (dependencies + container images) to CI quality gates.

## 5) Suggested success criteria

Use the following measurable criteria to track improvement:

- **CI lead time**: PR validation under agreed SLA (for example < 15 minutes for fast path).
- **Deployment safety**: 100% of production deploys linked to passing lint/test/smoke gates.
- **Service reliability**: p95 latency and error-rate SLOs tracked per critical service.
- **Integration stability**: contract test failures detected pre-merge rather than post-deploy.

## 6) Bottom line

The repository already demonstrates a credible foundation for a production-oriented multi-service platform: clear service decomposition, containerized infra, and meaningful operational scaffolding. The highest leverage next step is to tighten **quality gates + contract enforcement + orchestration parity** so that delivery becomes reliably repeatable as service count grows.
