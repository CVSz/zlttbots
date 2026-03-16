# DevOps Manual

## 1. Purpose

This manual is for infrastructure operators responsible for platform reliability, deployment, scaling, and recovery.

## 2. Standard lifecycle commands

### Build

```bash
docker compose build
```

### Deploy/start

```bash
docker compose up -d
```

### Validate runtime

```bash
docker compose ps
```

### Test baseline

```bash
pytest
```

## 3. Runtime topology reference

Infrastructure:

- `postgres`
- `redis`

Services:

- `viral-predictor`
- `market-crawler`
- `arbitrage-engine`
- `gpu-renderer`

Workers:

- `crawler-worker`
- `renderer-worker`
- `arbitrage-worker`

Ingress:

- `nginx`

## 4. Day-2 operations

### Tail logs

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
docker compose up -d --scale crawler-worker=5 --scale renderer-worker=3 --scale arbitrage-worker=3
```

## 5. Health diagnostics

Gateway probes:

```bash
curl -fS http://localhost/predict
curl -fS http://localhost/crawl
curl -fS http://localhost/arbitrage
```

Container status:

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

Deep-dive checks:

- Inspect dependency failures from startup logs.
- Validate DB connectivity from affected containers.
- Validate Redis availability when workers stall.

## 6. Backup and restore operations

### Backup

```bash
pg_dump -U zttato zttato > backup-$(date +%Y%m%d%H%M%S).sql
```

### Restore

```bash
psql -U zttato zttato < backup.sql
```

Recommended recovery order:

1. Restore/check `postgres` and `redis`.
2. Bring API services up and healthy.
3. Bring workers up and verify queue movement.
4. Verify ingress routes and user-facing paths.

## 7. Deployment safety rules

- Prefer incremental rollout over broad restarts during business hours.
- Keep rollback path prepared before high-risk deploys.
- Capture pre-change state (`ps`, logs, notable metrics).
- Execute post-change verification before closing deployment.

## 8. Suggested incident timeline

1. **Triage (0-10 min):** scope blast radius and affected services.
2. **Stabilize (10-30 min):** restore critical dependencies and ingress.
3. **Recover (30+ min):** restart/scale impacted workers/services.
4. **Validate:** run probes/tests and watch metrics.
5. **Postmortem:** document root cause, fixes, and prevention actions.
