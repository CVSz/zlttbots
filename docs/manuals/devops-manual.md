# DevOps Manual

## 1) Purpose

This manual is for infrastructure and platform engineers responsible for deployment, resilience, observability, scaling, and recovery across the zTTato repository.

## 2) Repository scope DevOps should understand

The project contains several layers:
- the default Docker Compose runtime
- optional PM2-managed Node services
- separate monitoring and PostgreSQL compose assets
- Kubernetes manifests for broader deployment scenarios
- Cloudflare and deployment helper scripts
- enterprise-maturity runtime code validated by tests

Do not assume every service in `services/` is part of the default Compose startup path.

## 3) Baseline lifecycle commands

### Build

```bash
docker compose build
```

### Deploy/start

```bash
docker compose up -d
```

### Inspect state

```bash
docker compose ps
```

### View logs

```bash
docker compose logs --tail=200 <service>
```

### Run tests

```bash
pytest
```

### Run repository smoke script

```bash
bash scripts/test-integration.sh
```

## 4) Current Compose topology

### Data plane
- PostgreSQL 15.8 with migration bootstrap
- Redis 7.4 with append-only mode

### API plane
- `viral-predictor` on `9100`
- `market-crawler` on `9400`
- `arbitrage-engine` on `9500`
- `gpu-renderer` on `9300`

### Worker plane
- `crawler-worker`
- `arbitrage-worker`
- `renderer-worker`

### Edge/gateway plane
- `nginx` on host port `80`

## 5) Supporting infrastructure included in the repo

### Monitoring
A dedicated monitoring compose file exists at `infrastructure/monitoring/docker-compose.monitoring.yml` for:
- Prometheus
- Grafana
- Loki
- Promtail

### PostgreSQL-only stack
A standalone PostgreSQL compose definition exists at `infrastructure/postgres/docker-compose.postgres.yml`.

### Kubernetes
The `infrastructure/k8s/` tree contains:
- namespace and config map resources
- deployments for admin panel, analytics, click-tracker, gpu-renderer, jwt-auth, and postgres
- services and ingress
- HPA/KEDA autoscaling manifests
- Kafka resources
- service-mesh and rate-limit resources
- JWT auth secret definitions
- Prometheus integration

### Cloudflare and automation
Cloudflare Terraform files and multiple deploy/repair scripts are available for non-local deployment paths.

## 6) Day-2 operations

### Restart one service

```bash
docker compose restart <service>
```

### Recreate one service

```bash
docker compose up -d --force-recreate <service>
```

### Scale workers

```bash
docker compose up -d --scale crawler-worker=5 --scale renderer-worker=3 --scale arbitrage-worker=3
```

### Inspect one service deeply

```bash
docker compose logs --tail=200 <service>
```

### Check runtime process table

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

## 7) Health diagnostics

### Gateway probes

```bash
curl -fS http://localhost/
curl -fS -X POST http://localhost/predict -H 'content-type: application/json' -d '{"views":1000,"likes":100,"comments":10,"shares":5}'
curl -fS -X POST http://localhost/crawl -H 'content-type: application/json' -d '{"keyword":"wireless earbuds"}'
curl -fS http://localhost/arbitrage
```

### Direct service probes

```bash
curl -fS http://localhost:9100/healthz
curl -fS http://localhost:9300/healthz
curl -fS http://localhost:9400/healthz
curl -fS http://localhost:9500/healthz
```

### Common fault-isolation logic
- if `/predict` fails, inspect PostgreSQL connectivity and predictor logs
- if `/crawl` or `/render` stalls, inspect Redis connectivity and worker logs
- if `/arbitrage` fails, inspect database state and arbitrage service logs
- if `/` fails, inspect Nginx health and upstream dependency status

## 8) Backup and restore

### Backup

```bash
pg_dump -U zttato zttato > backup-$(date +%Y%m%d%H%M%S).sql
```

### Restore

```bash
psql -U zttato zttato < backup.sql
```

Recommended sequence:
1. confirm backup integrity and environment target
2. stabilize or stop write-heavy services
3. restore PostgreSQL
4. bring API services up
5. bring workers up
6. run gateway and service smoke checks

## 9) Node-service operations

Use PM2-backed tooling for standalone Node apps:

```bash
bash scripts/zttato-node.sh install
bash scripts/zttato-node.sh start
bash scripts/zttato-node.sh status
bash scripts/zttato-node.sh logs
```

This path is separate from the default Compose runtime and should be documented per environment when enabled.

## 10) Deployment safety rules

- capture `docker compose ps` and key logs before changes
- prefer incremental rollout or targeted restarts over full-stack churn
- verify DB and Redis first during incident recovery
- decide explicitly whether renderer should run in CPU or GPU mode
- enable monitoring before relying on the platform in shared environments
- keep rollback scripts and restore procedures ready for any higher-risk change

## 11) Enterprise runtime context

The test suite validates a broader runtime model that includes service discovery, central queues, autoscaling, distributed crawler management, and GPU scheduling. Treat those modules as reference architecture and implementation guidance for future or alternate deployments rather than assuming they are all wired into the default Compose file today.
