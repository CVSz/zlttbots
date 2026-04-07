# Enterprise Production Maturity Roadmap

This roadmap converts the enterprise checklist into an execution-ready program for `zlttbots`.

## Prioritization model

- **P0 (Foundation / 0-30 days):** high risk-reduction and immediate governance controls.
- **P1 (Hardening / 31-60 days):** reliability and operational confidence improvements.
- **P2 (Optimization / 61-90 days):** advanced scaling and cost efficiency tuning.

## P0 - Foundation (0-30 days)

### Security & Compliance

1. **Centralized secrets management**
   - Integrate Vault or cloud secret manager and remove runtime `.env` dependency from production containers.
   - Enforce secret rotation policy and access via workload identity.
   - **Definition of done:** no production service reads secrets from plain files.

2. **SSO + RBAC for admin panel and internal APIs**
   - Add OIDC/SAML authentication and role mapping (`admin`, `operator`, `viewer`, `auditor`).
   - Gate privileged API routes with role-based policy middleware.
   - **Definition of done:** all privileged routes require role claims from IdP.

3. **Audit log pipeline for privileged actions**
   - Emit immutable audit events (`actor`, `action`, `resource`, `ip`, `timestamp`, `result`).
   - Store in append-only sink and add query dashboard for incident response.
   - **Definition of done:** privileged actions are traceable end-to-end.

4. **Automated SAST/DAST and container image scanning in CI**
   - Add SAST and dependency scan for Python/Node.
   - Add container image scanning for every image built in CI.
   - **Definition of done:** PRs fail on high/critical findings unless approved risk exception exists.

5. **CI/CD gates before deploy**
   - Require unit, integration, and security checks on pull requests.
   - Block deployment job unless required checks pass.
   - **Definition of done:** no merge to `main` without passing required gate matrix.

6. **Environment promotion workflow with approvals**
   - Define `dev -> staging -> production` pipeline stages.
   - Require approvers for production promotion.
   - **Definition of done:** production release is traceable to staged artifact and approval record.

### Reliability & Resilience

7. **Define and track SLOs per service**
   - Start with availability, p95 latency, and data freshness.
   - Add service error budgets and escalation policy on burn rate.
   - **Definition of done:** each production service has published SLO and owner.

8. **Circuit breakers, retries with backoff, idempotency keys**
   - Add resilient client wrappers for external dependency calls.
   - Apply idempotency keys to write operations and webhook ingestion.
   - **Definition of done:** transient external failures no longer cause cascading outages.

## P1 - Hardening (31-60 days)

### Observability & Operations

9. **Unified logs, metrics, traces (OpenTelemetry)**
   - Standardize telemetry SDK instrumentation and correlation IDs.
   - Publish service dashboards and cross-service trace views.
   - **Definition of done:** single dashboard can trace request path and failure cause.

10. **Runbooks for every production service and worker**
    - Add startup, troubleshooting, rollback, and escalation steps.
    - Include top-5 incident signatures and known fixes.
    - **Definition of done:** on-call can resolve common incidents from docs only.

11. **Alert routing with severity policy and ownership**
    - Define `SEV-1` to `SEV-4` severity policy.
    - Route alerts to primary and secondary on-call owners.
    - **Definition of done:** every alert has owner, severity, and response SLA.

12. **Capacity dashboards and error budget views**
    - Include queue depth, worker throughput, DB saturation, and error budgets.
    - Add trend and forecast panels for capacity planning.
    - **Definition of done:** weekly ops review uses these dashboards as source of truth.

13. **Synthetic checks for public and key internal paths**
    - Add scheduled synthetic probes for critical endpoints and worker pipelines.
    - Alert on availability and latency regression.
    - **Definition of done:** failures are detected before user-reported incidents.

### Delivery & Governance

14. **IaC policy checks for k8s and docker changes**
    - Add policy validation jobs for manifests and compose changes.
    - Enforce baseline controls (non-root, resource limits, image pinning).
    - **Definition of done:** noncompliant infra changes are blocked in CI.

15. **Versioned API contracts and compatibility verification**
    - Define contract repository and versioning rules.
    - Run backward-compatibility checks in CI.
    - **Definition of done:** breaking API changes require explicit major version process.

16. **Change management template for high-risk rollouts**
    - Standardize rollout plan, risk analysis, rollback, and sign-off.
    - Link each high-risk release to approved change record.
    - **Definition of done:** all high-risk deployments include completed template.

### Security & Compliance

17. **Data retention + PII controls**
    - Define retention classes and purge schedules.
    - Apply encryption at rest and field-level masking for sensitive data.
    - **Definition of done:** PII handling policy is documented and technically enforced.

## P2 - Optimization (61-90 days)

### Reliability & Resilience

18. **Multi-AZ database and Redis HA with failover playbooks**
    - Implement HA topology and test failover drills.
    - Document operator runbook and recovery steps.
    - **Definition of done:** failover drill meets availability target and runbook accuracy.

19. **Blue/green or canary deployments**
    - Introduce progressive rollout strategy for zero-downtime upgrades.
    - Add automated rollback trigger on SLO regression.
    - **Definition of done:** production upgrades can be partially released and safely reverted.

20. **Disaster recovery with RPO/RTO targets and drills**
    - Define per-service RPO/RTO and backup scope.
    - Run restore drills and publish evidence.
    - **Definition of done:** quarterly DR drill meets target objectives.

### Performance & Cost Control

21. **Autoscaling tuning with workload metrics**
    - Tune scaling thresholds using observed queue and request metrics.
    - Validate scale-up/down behavior under load tests.
    - **Definition of done:** autoscaling maintains SLO while minimizing overprovisioning.

22. **Workload profiling (Python/Node hot paths)**
    - Profile crawler, renderer, predictor, and API hot paths.
    - Implement code or concurrency optimizations from profile data.
    - **Definition of done:** measurable latency/throughput gains on target workloads.

23. **Cost allocation tags and cloud spend dashboard**
    - Apply standardized tags (`service`, `env`, `owner`, `cost_center`).
    - Publish spend dashboard with anomaly detection alerts.
    - **Definition of done:** monthly spend attributable per service with variance explanation.

24. **Queue prioritization and admission control**
    - Add priority classes and fairness limits for burst traffic.
    - Protect critical workloads from starvation.
    - **Definition of done:** critical queues maintain SLO under heavy burst load.

25. **Periodic rightsizing for compute-heavy services**
    - Review CPU/RAM/GPU allocation every release cycle.
    - Adjust instance types and worker counts from observed utilization.
    - **Definition of done:** compute utilization remains within target efficiency band.

## Cross-functional ownership matrix

- **Security team:** items 1-5, 17.
- **Platform/SRE:** items 7-13, 18-20.
- **Delivery/DevEx:** items 14-16.
- **Performance/FinOps:** items 21-25.

## Suggested milestone cadence

- **Milestone 1 (end of day 30):** P0 complete and enforced.
- **Milestone 2 (end of day 60):** P1 complete with operational handoff.
- **Milestone 3 (end of day 90):** P2 complete with measurable SLO and cost improvements.
