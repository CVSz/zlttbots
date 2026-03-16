# Admin Manual

## 1. Purpose

This manual is for platform administrators managing access, service health, and operational coordination.

## 2. Core responsibilities

- Maintain user/admin access workflows and policy enforcement.
- Monitor API health, worker throughput, and queue pressure.
- Coordinate incident triage and escalation with DevOps.
- Perform post-deploy verification and release acceptance checks.

## 3. Daily command baseline

### Start platform

```bash
docker compose up -d
```

### Stop platform

```bash
docker compose down
```

### Runtime status

```bash
docker compose ps
```

### Service logs

```bash
docker compose logs --tail=200 <service-name>
```

## 4. Service inventory and expectations

Critical infrastructure:

- `postgres`
- `redis`

Core APIs:

- `viral-predictor`
- `market-crawler`
- `arbitrage-engine`
- `gpu-renderer`

Workers:

- `crawler-worker`
- `renderer-worker`
- `arbitrage-worker`

Gateway:

- `nginx`

## 5. Health and reachability checks

### API gateway checks

```bash
curl -i http://localhost/predict
curl -i http://localhost/crawl
curl -i http://localhost/arbitrage
```

### Container-level checks

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

## 6. Worker capacity management

Scale workers during backlog or SLA pressure:

```bash
docker compose up -d --scale crawler-worker=3 --scale renderer-worker=2 --scale arbitrage-worker=2
```

Operational guidance:

- Increase replicas gradually.
- Re-check host CPU/memory before further increases.
- Roll back scale if saturation causes unstable latency.

## 7. Backup and data protection

### Backup

```bash
pg_dump -U zttato zttato > backup-$(date +%Y%m%d%H%M%S).sql
```

### Restore

```bash
psql -U zttato zttato < backup.sql
```

Admin checklist before restore:

1. Freeze or reduce write-heavy traffic.
2. Confirm backup provenance and timestamp.
3. Coordinate maintenance window with stakeholders.
4. Validate post-restore API behavior.

## 8. Incident response (admin layer)

1. Detect and scope impact.
2. Capture evidence (`ps`, logs, endpoint checks).
3. Apply low-risk corrective actions (targeted restart/scale).
4. Escalate infra-level issues to DevOps with artifacts.
5. Publish status updates and resolution summary.

## 9. Release acceptance checklist

After deployments:

- Confirm all critical services are healthy.
- Confirm route reachability through nginx.
- Confirm no immediate spike in 5xx rates.
- Confirm worker queues are moving.
- Confirm dashboard/operator paths are usable.
