# Current Project Review and What We Need Next

This document is a practical review of the current `zttato-platform` repository and a clear execution plan for the next phase.

## 1) Current snapshot (what we already have)

### Platform and runtime foundation
- Central orchestration with `docker-compose.yml` including PostgreSQL, Redis, API services, workers, and NGINX reverse proxy.
- Service-level health checks are already configured in Compose for critical services.
- Startup and shutdown scripts exist at repository root (`start.sh`, `stop.sh`) and in `scripts/`.

### Service landscape
- Python API services with Uvicorn entrypoints:
  - `viral-predictor`
  - `market-crawler`
  - `arbitrage-engine`
  - `gpu-renderer`
- Node.js services present for analytics, tracking, farming, uploader, and crawler/miner workflows.
- Admin panel service exists with Next.js stack and component structure.

### Engineering and operations assets
- CI workflow exists under `.github/workflows/zttato-ci.yml`.
- Operational docs exist for backup, monitoring, logging, and disaster recovery.
- Integration smoke-test script exists (`scripts/test-integration.sh`).
- Repository validation script exists (`infrastructure/scripts/validate-repo.sh`).

---

## 2) Key strengths

1. **Good infrastructure baseline**
   - Compose topology, health checks, and dependency ordering are already in place.
2. **Service decomposition is clear**
   - Domain responsibilities are separated into individual services.
3. **Operations-first mindset**
   - Runbooks and operational documentation are already started.
4. **Automation hooks already exist**
   - There are scripts for diagnostics, deployment, repair, and integration checks.

---

## 3) Current gaps that block production maturity

1. **Quality gates are not consistently enforced**
   - Validation scripts exist, but there is no clear mandatory CI gate matrix (lint + unit + integration + contract).
2. **Cross-service contracts need stronger control**
   - APIs and payload schemas are documented, but strict contract verification should be expanded to prevent integration drift.
3. **Observability still needs standardization**
   - Need consistent correlation IDs, structured logs, and agreed service-level SLO dashboards.
4. **Security baseline needs hard enforcement**
   - Secret lifecycle, image/dependency scanning, and policy checks should be mandatory on pipeline.
5. **Release governance and ownership model need formalization**
   - Need explicit ownership, definition of done per service, and release readiness checklist.

---

## 4) What we need next (priority roadmap)

## Priority A (Week 1): Reliability hardening

- Standardize `/healthz` and `/readyz` response shape for all HTTP services.
- Add readiness/liveness parity between Docker Compose and Kubernetes manifests.
- Define one owner per service and add on-call routing metadata.
- Add a single command to run baseline checks locally (syntax + smoke + docs link checks).

**Exit criteria:**
- Every API service has deterministic health endpoints.
- Failures are visible through one dashboard or one aggregated health report.

## Priority B (Week 2): CI quality gates and contract safety

- Enforce mandatory CI stages: lint, syntax, unit tests, integration smoke tests.
- Add contract tests for high-risk service boundaries:
  - crawler -> analytics
  - uploader -> analytics
  - predictor -> downstream storage/reporting
- Block merge on contract or integration failures.

**Exit criteria:**
- No PR can merge if service contracts break.
- Main branch always deployable from latest commit.

## Priority C (Week 3): Observability and incident response

- Introduce correlation ID propagation in all APIs/workers.
- Normalize JSON logging fields (`service`, `env`, `trace_id`, `request_id`, `latency_ms`, `status`).
- Publish SLO dashboards for p95 latency, error rate, throughput.
- Create incident playbooks for top-5 failure scenarios.

**Exit criteria:**
- One request can be traced end-to-end in logs.
- Incident triage starts with a documented playbook and measured SLO status.

## Priority D (Week 4): Security and release governance

- Move secrets to managed secret mechanism (not plain env committed workflows).
- Add dependency and container image scanning in CI.
- Define release checklist: migration safety, rollback, smoke tests, post-deploy checks.
- Add versioned changelog discipline for all production deployments.

**Exit criteria:**
- Security checks run on every PR and release branch.
- Every deployment has rollback-ready evidence and post-release verification.

---

## 5) Ready-to-implement backlog (copy into tickets)

1. Create `service-readiness-spec.md` with standard `/healthz` + `/readyz` response contract.
2. Add `ci-quality-gates` job matrix to `.github/workflows/zttato-ci.yml`.
3. Add contract-test suite for three critical service-to-service flows.
4. Add structured logging middleware/template for Python and Node services.
5. Add `docs/operations/release-checklist.md` and `docs/operations/oncall-ownership.md`.
6. Add secret scanning and image scanning steps in CI.
7. Add dashboard definition doc (`docs/operations/slo-dashboard.md`).

---

## 6) Recommended operating cadence

- **Weekly architecture review (30 min):** risks, bottlenecks, contract drift.
- **Weekly reliability review (30 min):** incidents, SLO trend, top flaky services.
- **Release review per deploy:** checklist + rollback confirmation.

---

## 7) Executive summary

The project already has a strong platform skeleton (multi-service architecture, orchestration, and operations scripts). The next step is to convert that foundation into **production-grade discipline**: strict quality gates, enforceable service contracts, standardized observability, and security governance.

If we execute Priority A-D in sequence, we move from “functional platform” to “repeatably reliable platform” with lower incident risk and faster safe delivery.
