# DevOps Manual

This manual is the full-detail infrastructure and runtime operations guide for zTTato Platform.

## 1) DevOps responsibilities

DevOps owns the reliability envelope across:
- Docker Compose runtime
- optional Node service fleet
- monitoring and logging stack
- PostgreSQL and backup/restore workflows
- deployment and recovery automation
- Kubernetes and Cloudflare paths where enabled
- production-hardening decisions for the extended service graph

## 2) Repository scope you must keep straight

The repository contains four overlapping layers:

1. **baseline local runtime** — safest starting environment
2. **extended Compose control plane** — many internal services declared in the main Compose file
3. **PM2-managed Node apps** — separate runtime path from the baseline gateway
4. **enterprise blueprint modules** — validated by tests but not automatically surfaced by nginx

Document which layer you are operating before making changes or writing runbooks.

## 3) Baseline lifecycle commands

```bash
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail=200 <service>
pytest
bash scripts/test-integration.sh
bash infrastructure/scripts/validate-repo.sh
```

## 4) Compose topology summary

### Stateful layer
- PostgreSQL 15.8 with migration bootstrap
- Redis 7.4 with append-only mode
- Redpanda for event-stream workflows in the extended stack

### Public-edge layer
- nginx on host port `80`

### Baseline API layer
- `viral-predictor` on internal port `9100`
- `market-crawler` on internal port `9400`
- `arbitrage-engine` on internal port `9500`
- `gpu-renderer` on internal port `9300`

### Extended internal API/control-plane layer
- `tenant-service` on `8000`
- `affiliate-webhook` on `9700`
- `execution-engine` on `9600`
- many additional platform services, mostly on internal `8000`

### Distributed/ML helpers
- `ray-head` with host port `8265`
- `ray-worker`
- RL/model/feature services

## 5) Health diagnostics

### Gateway probes

```bash
curl -fS http://localhost/
curl -fS -X POST http://localhost/predict -H 'content-type: application/json' -d '{"views":1000,"likes":100,"comments":10,"shares":5}'
curl -fS -X POST http://localhost/crawl -H 'content-type: application/json' -d '{"keyword":"wireless earbuds"}'
curl -fS http://localhost/arbitrage
```

### Service-level probes

```bash
curl -fS http://localhost:9100/healthz || true
curl -fS http://localhost:9300/healthz || true
curl -fS http://localhost:9400/healthz || true
curl -fS http://localhost:9500/healthz || true
```

### Fault-isolation logic
- if predictor fails, inspect PostgreSQL and `viral-predictor`
- if crawler/render stalls, inspect Redis and worker logs
- if arbitrage fails, inspect PostgreSQL and arbitrage worker freshness
- if gateway fails, inspect nginx and upstream readiness
- if extended services fail, verify their transitive dependencies, especially Redpanda, Ray, and internal service health order

## 6) Day-2 operations

### Restart or recreate one service

```bash
docker compose restart <service>
docker compose up -d --force-recreate <service>
```

### Scale baseline workers

```bash
docker compose up -d --scale crawler-worker=5 --scale renderer-worker=3 --scale arbitrage-worker=3
```

### Capture runtime table

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

## 7) Supporting infrastructure in the repo

### Monitoring
Start separately when needed:

```bash
docker compose -f infrastructure/monitoring/docker compose.monitoring.yml up -d
```

Provides:
- Prometheus
- Grafana
- Loki
- Promtail

### PostgreSQL-only stack
Standalone database compose path:

```bash
docker compose -f infrastructure/postgres/docker compose.postgres.yml up -d
```

### Kubernetes
The `infrastructure/k8s/` tree includes:
- namespace/config resources
- deployments and services
- ingress
- HPA/KEDA manifests
- Kafka, JWT auth, monitoring, and mesh assets
- multi-region examples

### Cloudflare / edge automation
Cloudflare tunnel and edge-related scripts/configs exist under `scripts/`, `cloudflare-devops/`, and `infrastructure/cloudflare/`.

## 8) Node-service operations

```bash
bash scripts/zttato-node.sh install
bash scripts/zttato-node.sh start
bash scripts/zttato-node.sh stop
bash scripts/zttato-node.sh restart
bash scripts/zttato-node.sh status
bash scripts/zttato-node.sh logs
```

If PM2 is missing, the wrapper will fail for status/log actions. Treat PM2 availability as an environment prerequisite for that mode.

## 9) Backup and restore

### Backup

```bash
pg_dump -U zttato zttato > backup-$(date +%Y%m%d%H%M%S).sql
```

### Restore

```bash
psql -U zttato zttato < backup.sql
```

Recommended sequence:
1. verify environment target
2. stabilize or stop heavy-write services
3. restore DB
4. bring APIs up
5. bring workers up
6. run smoke checks
7. confirm logs and monitoring look normal

## 10) Deployment safety rules

- validate `docker compose config` after env or graph changes
- keep gateway exposure intentionally narrow
- confirm internal-only services are not exposed without auth and ownership
- prefer targeted restarts over full-stack churn
- verify stores before app tiers during incidents
- keep rollback and restore procedures ready for every high-risk change
- remember that the extended Compose graph may consume significantly more host resources than the baseline subset

## 11) Enterprise runtime context

The tests validate broader patterns including service discovery, autoscaling, crawler clustering, queue systems, and GPU scheduling. Use these modules as implementation guidance or alternate deployment building blocks, but do not assume they are all activated through the day-one gateway path.
