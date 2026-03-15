# DevOps Manual

## 1. Purpose

This manual is for infrastructure operators responsible for platform reliability, deployment, and recovery.

## 2. Baseline commands

### Build

```bash
docker compose build
```

### Start

```bash
docker compose up -d
```

### Validate runtime

```bash
docker compose ps
```

### Test

```bash
pytest
```

## 3. Runtime topology

- Data: `postgres`, `redis`
- API/compute: predictor, crawler, arbitrage, renderer
- Workers: `crawler-worker`, `renderer-worker`, `arbitrage-worker`
- Gateway: `nginx`

## 4. Operational playbook

### Logs

```bash
docker compose logs --tail=200 <service>
```

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
docker compose up -d --scale crawler-worker=5
```

## 5. Health diagnostics

```bash
curl -fS http://localhost/predict
curl -fS http://localhost/crawl
curl -fS http://localhost/arbitrage
```

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

## 6. Backup and recovery

### Backup

```bash
pg_dump -U zttato zttato > backup-$(date +%Y%m%d%H%M%S).sql
```

### Restore

```bash
psql -U zttato zttato < backup.sql
```

Recovery order:

1. Restore `postgres` and `redis`
2. Restore API services
3. Restore workers
4. Validate ingress and external routing

## 7. Reliability recommendations

- Enforce alerting on service health and queue lag.
- Run periodic restore drills.
- Use staged rollout for high-risk changes.
- Keep runbooks and ownership maps current.
