
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

---

## Roadmap

- distributed queue architecture
- service discovery
- GPU cluster orchestration
- CI/CD automation
- Kubernetes multi-node support
- observability stack

---

License: Private internal infrastructure project
