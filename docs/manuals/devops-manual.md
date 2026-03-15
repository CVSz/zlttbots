# DevOps Manual

## 1. Purpose

This manual is for DevOps engineers owning deployment, reliability, scaling, and recovery of zTTato Platform.

---

## 2. Stack Summary

- Container orchestration: Docker Compose
- Services: Node.js + Python microservices
- Data stores: PostgreSQL + Redis
- Entry gateway: Nginx
- Optional edge automation: Cloudflare scripts/tooling

---

## 3. Build, Boot, and Validate

### Build images

```bash
docker compose build
```

### Start full stack

```bash
docker compose up -d
```

### Validate running services

```bash
docker compose ps
```

### Run repository tests

```bash
pytest
```

---

## 4. Runtime Topology

Core compose services:

- data: `postgres`, `redis`
- APIs: `viral-predictor`, `market-crawler`, `arbitrage-engine`, `gpu-renderer`
- workers: `crawler-worker`, `arbitrage-worker`, `renderer-worker`
- edge/gateway: `nginx`

Network: `zttato-net`

Persistent volumes:

- `postgres_data`
- `redis_data`

---

## 5. Environment and Configuration

### Required config artifacts

- `.env` (runtime configuration)
- `configs/nginx.conf` (reverse proxy config)
- `configs/env/production.env` (production-oriented defaults)

### Key dependencies between services

- DB-backed services depend on healthy `postgres`.
- Queue-based services/workers depend on healthy `redis`.
- `nginx` depends on predictor/crawler/arbitrage health checks.

---

## 6. Operational Playbook

### Service logs

```bash
docker compose logs --tail=200 <service>
```

### Restart single service

```bash
docker compose restart <service>
```

### Recreate one service

```bash
docker compose up -d --force-recreate <service>
```

### Scale workers

```bash
docker compose up -d --scale crawler-worker=5
```

---

## 7. Verification and Diagnostics

### API checks

```bash
curl -fS http://localhost/predict
curl -fS http://localhost/crawl
curl -fS http://localhost/arbitrage
```

### Container health perspective

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

### Scripted diagnostics

Repository includes operational scripts under `scripts/` (doctor, monitor, repair, deploy, restart).
Use them for standardized troubleshooting and environment repair.

---

## 8. Deployment Guidance

### Standard deploy

```bash
docker compose up -d
```

### Safer deploy sequence

1. Pull latest code and review config diffs.
2. Build images.
3. Apply deployment.
4. Validate health checks and endpoints.
5. Monitor logs for at least one processing window.

---

## 9. Backup and Recovery

### Backup data

```bash
pg_dump -U zttato zttato > backup.sql-$(date +%Y%m%d%H%M%S)
```

### Restore data

```bash
psql -U zttato zttato < backup.sql
```

### Recovery priorities

1. Restore database availability.
2. Restore queue/cache path.
3. Restore API services.
4. Restore workers.
5. Validate ingress and external routing.

---

## 10. Hardening and Reliability Recommendations

- Add centralized logs and metrics (e.g., ELK, Loki, Prometheus).
- Set explicit alerting on health checks and queue lag.
- Automate backup retention and periodic restore drills.
- Use staged environments before production rollouts.
- Pin dependencies and image tags for reproducible deployments.
