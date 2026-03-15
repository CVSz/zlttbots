
# zTTato Platform

zTTato Platform is a modular automation and growth infrastructure designed for large-scale social commerce and affiliate operations.
It combines Node.js services, Python compute services, AI pipelines, and data crawlers with containerized infrastructure,
orchestration tooling, and edge networking integration.

The platform is designed for:
- TikTok automation pipelines
- Social commerce intelligence
- AI-generated media production
- Market arbitrage detection
- Large-scale crawler operations
- Growth analytics and prediction

Architecture: microservice-oriented with independent services communicating through APIs, queues, and shared infrastructure.

---

## Architecture Overview

Layer | Technology | Purpose
----- | ---------- | -------
API Services | Node.js | REST APIs and automation logic
Compute Services | Python | ML, crawling, arbitrage engines
Queue & Cache | Redis | Worker communication and job queues
Database | PostgreSQL | Persistent data storage
Infrastructure | Docker / Kubernetes | Container orchestration
Edge | Cloudflare | DNS, tunnels, and edge networking
UI | React | Admin control panel

---

## Repository Structure

.
├── docker-compose.yml
├── start-zttato.sh
├── env.edge
├── cloudflare-devops/
├── infrastructure/
│   ├── ci/
│   ├── k8s/
│   ├── postgres/
│   ├── scripts/
│   └── start/
├── scripts/
└── services/
    ├── account-farm
    ├── admin-panel
    ├── ai-video-generator
    ├── analytics
    ├── arbitrage-engine
    ├── click-tracker
    ├── gpu-renderer
    ├── market-crawler
    ├── shopee-crawler
    ├── tiktok-farm
    ├── tiktok-shop-miner
    └── viral-predictor

---

## Quick Start

Prerequisites
- Docker
- Docker Compose
- Node.js
- Python 3
- Git

Bootstrap:

bash start-zttato.sh

The bootstrap script:
- fixes script permissions
- installs dependencies
- starts postgres/redis
- builds containers
- runs migrations
- starts workers
- performs health checks

---

## Manual Validation

Shell syntax check

while IFS= read -r f; do bash -n "$f"; done < <(rg --files -g '*.sh')

Python syntax

python -m compileall services

JSON validation

while IFS= read -r f; do python -m json.tool "$f" >/dev/null; done < <(rg --files -g 'package.json')

---

## Running the Platform

Start

./start.sh

Check services

docker compose ps

Stop

./stop.sh

---

## API Endpoints

/predict
/crawl
/arbitrage

Example:

http://SERVER/predict
http://SERVER/crawl
http://SERVER/arbitrage

---

## Worker Scaling

docker compose up -d --scale crawler-worker=5

---

## Backup

pg_dump -U zttato zttato > backup.sql

Restore

psql -U zttato zttato < backup.sql

---

## Documentation

docs/development/current-status-and-next-steps.md
docs/operations/health-checks.md
scripts/test-integration.sh
docs/manuals/user-manual.md
docs/manuals/admin-manual.md
docs/manuals/devops-manual.md
docs/manuals/godmode-manual.md

---

## Roadmap

- distributed queue architecture
- service discovery
- GPU cluster orchestration
- CI/CD automation
- Kubernetes multi-node support
- observability stack

---

## Enterprise Production Advancement Backlog

Use this list to prioritize what should be added next for enterprise-grade production maturity.

### Security & Compliance

- [ ] Centralized secrets management (Vault / cloud secret manager), replacing plain env files in runtime.
- [ ] SSO + RBAC for admin panel and internal APIs (OIDC/SAML).
- [ ] Audit log pipeline for privileged actions (who did what, when, from where).
- [ ] Automated SAST/DAST and container image scanning in CI.
- [ ] Data retention + PII controls (encryption at rest, field-level masking, policy docs).

### Reliability & Resilience

- [ ] Define and track SLOs (availability, latency, data freshness) per service.
- [ ] Add circuit breakers, retries with backoff, and idempotency keys for external calls.
- [ ] Multi-AZ database and Redis HA setup with tested failover playbooks.
- [ ] Blue/green or canary deploy strategy for zero-downtime upgrades.
- [ ] Disaster recovery plan with RPO/RTO targets and regular restore drills.

### Observability & Operations

- [ ] Unified logs, metrics, and tracing (OpenTelemetry + centralized dashboard).
- [ ] Service-level runbooks for every production service and worker.
- [ ] Alert routing with severity policy and on-call ownership.
- [ ] Capacity dashboards (queue depth, worker throughput, DB saturation, error budgets).
- [ ] Synthetic checks for public endpoints and key internal worker paths.

### Delivery & Governance

- [ ] CI/CD gates: unit/integration/security checks required before deploy.
- [ ] Environment promotion workflow (dev -> staging -> production) with approvals.
- [ ] Infrastructure-as-Code policy checks for k8s and docker changes.
- [ ] Versioned API contracts with backward-compatibility verification.
- [ ] Change management template for high-risk rollouts.

### Performance & Cost Control

- [ ] Autoscaling policy tuning using real workload metrics.
- [ ] Workload profiling for Python/Node hot paths and crawler throughput.
- [ ] Cost allocation tags per service and dashboard for cloud spend visibility.
- [ ] Queue prioritization and admission control for burst traffic.
- [ ] Periodic rightsizing review for compute-heavy services (GPU/ML/rendering).

## Already Implemented in This Project (Current Baseline)

- [x] Containerized microservices architecture with Docker Compose and service isolation.
- [x] Kubernetes deployment artifacts (deployments, services, ingress, autoscaling manifests).
- [x] Automated platform scripts for bootstrap, rollback, repair, and diagnostics.
- [x] Worker model separated by domain (crawler-worker, renderer-worker, arbitrage-worker).
- [x] PostgreSQL + Redis split for persistence and queue/cache responsibilities.
- [x] Cloudflare edge/devops helper tooling for DNS and tunnel operations.

---

License: Private internal infrastructure project
