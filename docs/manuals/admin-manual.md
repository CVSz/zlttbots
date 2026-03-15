# Admin Manual

## 1. Purpose

This manual is for platform administrators managing access, service health, and operational coordination.

## 2. Core responsibilities

- Maintain dashboard/user access controls.
- Monitor API and worker health.
- Coordinate incident triage and escalation.
- Validate post-deploy platform integrity.

## 3. Start, stop, and status

### Start

```bash
docker compose up -d
```

### Stop

```bash
docker compose down
```

### Status

```bash
docker compose ps
```

## 4. Service inventory to watch

- `postgres`, `redis`
- `viral-predictor`, `market-crawler`, `arbitrage-engine`, `gpu-renderer`
- `crawler-worker`, `renderer-worker`, `arbitrage-worker`
- `nginx`

## 5. Operational checks

### Logs

```bash
docker compose logs --tail=200 <service-name>
```

### API route reachability

```bash
curl -i http://localhost/predict
curl -i http://localhost/crawl
curl -i http://localhost/arbitrage
```

## 6. Worker scaling

```bash
docker compose up -d --scale crawler-worker=3 --scale renderer-worker=2 --scale arbitrage-worker=2
```

Adjust replicas according to queue depth, SLA pressure, and host capacity.

## 7. Data protection

### Backup

```bash
pg_dump -U zttato zttato > backup-$(date +%Y%m%d%H%M%S).sql
```

### Restore

```bash
psql -U zttato zttato < backup.sql
```

## 8. Incident response (admin layer)

1. Detect and scope the issue.
2. Gather evidence (`docker compose ps`, logs, endpoint status).
3. Apply safe restarts if low risk.
4. Escalate infra-level issues to DevOps with artifacts.
