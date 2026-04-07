# Admin Manual

This manual is the full-detail operating guide for administrators who own daily platform usability, operator support, and basic runtime health.

## 1) Admin scope

Admins are usually responsible for:
- keeping the baseline platform reachable
- confirming user-facing routes work
- checking worker backlog symptoms
- supervising optional admin-panel access
- coordinating incidents with DevOps or godmode operators when deeper infrastructure action is needed

## 2) Service inventory admins should know

### Baseline data services
- `postgres`
- `redis`

### Baseline APIs
- `viral-predictor`
- `market-crawler`
- `arbitrage-engine`
- `gpu-renderer`

### Baseline workers
- `crawler-worker`
- `arbitrage-worker`
- `renderer-worker`

### Gateway
- `nginx`

### Extended services you may hear about
- `tenant-service`
- `affiliate-webhook`
- `execution-engine`
- `reward-collector`
- `feature-store`
- `model-service`
- `master-orchestrator`

### Optional Node application layer
- `admin-panel`
- `analytics`
- `click-tracker`
- other PM2-managed Node services where enabled

## 3) Daily command baseline

### Start or refresh the platform

```bash
docker compose up -d
```

### Stop the platform

```bash
docker compose down
```

### Inspect status

```bash
docker compose ps
```

### Inspect logs

```bash
docker compose logs --tail=200 <service-name>
```

### Inspect runtime container table

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

## 4) Standard admin health checks

### Gateway probes

```bash
curl -i http://localhost/
curl -i -X POST http://localhost/predict -H 'content-type: application/json' -d '{"views":1000,"likes":100,"comments":10,"shares":5}'
curl -i -X POST http://localhost/crawl -H 'content-type: application/json' -d '{"keyword":"wireless earbuds"}'
curl -i http://localhost/arbitrage
```

### Direct service checks when isolating faults

```bash
curl -i http://localhost:9100/healthz || true
curl -i http://localhost:9300/healthz || true
curl -i http://localhost:9400/healthz || true
curl -i http://localhost:9500/healthz || true
```

## 5) Queue and worker management

Crawler and renderer workloads rely on Redis-backed queueing. Arbitrage also has a worker process.

### Scale workers

```bash
docker compose up -d --scale crawler-worker=3 --scale renderer-worker=2 --scale arbitrage-worker=2
```

Admin guidance:
- scale gradually
- watch CPU and memory after each change
- check worker logs after scaling
- if the platform becomes less stable after scaling, revert quickly

## 6) Support playbooks

### User cannot reach the gateway
1. run `docker compose ps`
2. confirm `nginx` is healthy
3. inspect `docker compose logs --tail=200 nginx`
4. test `curl -i http://localhost/`

### User reports predictor errors
1. inspect `viral-predictor` logs
2. verify PostgreSQL health
3. test with a known-good request body

### User reports delayed crawl execution
1. inspect `market-crawler` logs
2. inspect `crawler-worker` logs
3. confirm Redis health
4. look for repeated queue backlog symptoms

### User reports stale arbitrage results
1. verify PostgreSQL health
2. inspect `arbitrage-engine` logs
3. inspect `arbitrage-worker` logs
4. escalate if ingestion or DB freshness appears broken

### User reports admin-panel issues
1. confirm the Node-service path is actually enabled
2. run `bash scripts/zlttbots-node.sh status`
3. inspect PM2 logs or generated log files
4. verify the correct credentials/environment URL are being used

## 7) Optional Node-service administration

### Install Node dependencies

```bash
bash scripts/zlttbots-node.sh install
```

### Start Node services

```bash
bash scripts/zlttbots-node.sh start
```

### Check PM2 state

```bash
bash scripts/zlttbots-node.sh status
```

### View logs

```bash
bash scripts/zlttbots-node.sh logs
bash scripts/zlttbots-node.sh logs admin-panel
```

## 8) Backup and restore basics

### Backup

```bash
pg_dump -U zlttbots zlttbots > backup-$(date +%Y%m%d%H%M%S).sql
```

### Restore

```bash
psql -U zlttbots zlttbots < backup.sql
```

Before restore:
- confirm source and timestamp
- coordinate downtime or reduced-write window
- run smoke checks after restore

## 9) Release acceptance checklist

After deployment or restart:
- confirm baseline services are running
- confirm gateway root works
- confirm `/predict`, `/crawl`, and `/arbitrage` respond
- confirm workers remain healthy after warm-up
- confirm DB and Redis show no obvious health failures
- confirm Node services are healthy if your environment uses them

## 10) Escalation rules

Escalate to DevOps or godmode if:
- DB or Redis is unstable
- multiple services are crash-looping
- the wider Compose dependency graph is degraded
- restore, rollback, or infrastructure changes are required
- exposure/auth questions arise for internal-only services
