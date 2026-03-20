# Admin Manual

## 1) Purpose

This manual is for platform administrators responsible for day-to-day availability, user support, and operational coordination in the current zTTato stack.

## 2) What admins own

Admins are typically responsible for:
- keeping the default Compose stack healthy
- verifying gateway/API reachability
- watching worker throughput and queue pressure
- supporting users with access or workflow issues
- coordinating with DevOps for deeper infrastructure or deployment work

## 3) Current baseline service inventory

### Data services
- `postgres`
- `redis`

### API services
- `viral-predictor`
- `market-crawler`
- `arbitrage-engine`
- `gpu-renderer`

### Background workers
- `crawler-worker`
- `arbitrage-worker`
- `renderer-worker`

### Gateway
- `nginx`

### Optional managed Node applications
Admins may also be asked to supervise PM2-managed Node services started through `scripts/zttato-node.sh`, especially `admin-panel` and analytics-related services.

## 4) Daily command baseline

### Start the platform

```bash
docker compose up -d
```

### Stop the platform

```bash
docker compose down
```

### Inspect state

```bash
docker compose ps
```

### Inspect logs

```bash
docker compose logs --tail=200 <service-name>
```

### Inspect container runtime status

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

## 5) Reachability and health checks

### Gateway root check

```bash
curl -i http://localhost/
```

### API checks through Nginx

```bash
curl -i -X POST http://localhost/predict \
  -H 'content-type: application/json' \
  -d '{"views":1000,"likes":100,"comments":10,"shares":5}'

curl -i -X POST http://localhost/crawl \
  -H 'content-type: application/json' \
  -d '{"keyword":"wireless earbuds"}'

curl -i http://localhost/arbitrage
```

### Direct health checks when isolating faults
- predictor: `http://localhost:9100/healthz`
- crawler: `http://localhost:9400/healthz`
- renderer: `http://localhost:9300/healthz`
- arbitrage: `http://localhost:9500/healthz`

## 6) Worker and queue management

The crawler and renderer depend on Redis-backed queueing, and the arbitrage engine includes its own worker process.

### Scale worker replicas

```bash
docker compose up -d --scale crawler-worker=3 --scale renderer-worker=2 --scale arbitrage-worker=2
```

Guidance:
- increase capacity gradually
- monitor CPU and memory after each change
- check logs after scaling to confirm workers actually start and consume work

## 7) User support playbook

### User cannot access the gateway
1. run `docker compose ps`
2. verify `nginx` is running
3. check `docker compose logs --tail=200 nginx`
4. test `curl -i http://localhost/`

### User reports scoring failures
1. check `viral-predictor` logs
2. confirm PostgreSQL is healthy
3. test the `/predict` route with a known-good payload

### User reports crawling delays
1. check `market-crawler` and `crawler-worker` logs
2. confirm Redis is healthy
3. see whether queue pressure or worker failures are visible

### User reports stale arbitrage data
1. verify PostgreSQL availability
2. inspect whether `arbitrage_events` has recent inserts
3. escalate to DevOps if ingestion or upstream workflows appear broken

## 8) Backup and restore basics

### Backup

```bash
pg_dump -U zttato zttato > backup-$(date +%Y%m%d%H%M%S).sql
```

### Restore

```bash
psql -U zttato zttato < backup.sql
```

Checklist before restore:
1. confirm backup source and timestamp
2. coordinate a maintenance window if needed
3. reduce write-heavy traffic where possible
4. run post-restore smoke checks immediately

## 9) Optional Node-service administration

### Install dependencies

```bash
bash scripts/zttato-node.sh install
```

### Start services

```bash
bash scripts/zttato-node.sh start
```

### Check PM2 status

```bash
bash scripts/zttato-node.sh status
```

### View service logs

```bash
bash scripts/zttato-node.sh logs
bash scripts/zttato-node.sh logs admin-panel
```

## 10) Release acceptance checklist

After any deployment or restart:
- confirm all baseline Compose services are running
- confirm root gateway health works
- confirm `/predict`, `/crawl`, and `/arbitrage` respond
- confirm workers remain up after initial warm-up
- confirm no obvious DB or Redis health failures in logs
- confirm optional Node services, if used, are healthy in PM2
