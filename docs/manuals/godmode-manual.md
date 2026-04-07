# Godmode Manual

This manual is the full-detail break-glass guide for severe zlttbots incidents. Godmode is for platform-wide recovery, failed deployments, data-risk events, or situations where admin/standard DevOps actions are not enough.

## 1) Rules of engagement

- restrict access tightly
- log every action with timestamp and reason
- prefer the smallest effective action
- capture system state before destructive changes
- define rollback/containment expectations before acting

## 2) What godmode can control

A godmode operator may:
- rebuild and restart the full Compose stack
- isolate, restart, or scale services aggressively
- operate database backup/restore workflows
- use repair, diagnostic, bootstrap, rollback, and doctor scripts
- manage Node, monitoring, Cloudflare, or alternate runtime tooling when the incident environment uses them
- contain public exposure issues by disabling or narrowing edge paths

## 3) Mandatory pre-action capture

Before taking major action, collect:

```bash
docker compose ps
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker compose logs --tail=200 nginx
docker compose logs --tail=200 postgres
docker compose logs --tail=200 redis
```

Also identify:
- whether the issue is DB, Redis, gateway, worker, extended-service, or edge related
- whether there is data-loss risk
- whether a maintenance notice is required

## 4) Full-stack control operations

### Build and deploy

```bash
docker compose build
docker compose up -d
```

### Controlled full restart

```bash
docker compose down
docker compose up -d
```

### Emergency stop

```bash
docker compose down
```

### Validate state after action

```bash
docker compose ps
curl -fS http://localhost/ || true
```

## 5) High-pressure scaling

When backlogs require emergency worker increases:

```bash
docker compose up -d --scale crawler-worker=5 --scale renderer-worker=3 --scale arbitrage-worker=3
```

Guidance:
- scale in steps when possible
- inspect host pressure after every scale-up
- undo the change if it worsens restart churn or latency

## 6) Recovery toolkit

Useful scripts include:
- `scripts/test-integration.sh`
- `scripts/zlttbots-doctor.sh`
- `scripts/repair-platform.sh`
- `scripts/zlttbots-docker-recovery.sh`
- `scripts/fix-zlttbots-stack.sh`
- `infrastructure/scripts/validate-repo.sh`
- `infrastructure/scripts/rollback.sh`
- `infrastructure/scripts/bootstrap-platform.sh`
- `infrastructure/scripts/full-source-scan.sh`

Prefer using an existing script over ad hoc shell when the script already matches the need.

## 7) Data operations

### Backup

```bash
pg_dump -U zlttbots zlttbots > backup-$(date +%Y%m%d%H%M%S).sql
```

### Restore

```bash
psql -U zlttbots zlttbots < backup.sql
```

Before restore:
- verify backup provenance and age
- stop or reduce write-heavy traffic
- decide whether a full-stack stop is necessary
- prepare post-restore validation commands

## 8) Optional environment-control paths

### Monitoring stack

```bash
docker compose -f infrastructure/monitoring/docker compose.monitoring.yml up -d
```

### Node-service lifecycle

```bash
bash scripts/zlttbots-node.sh install
bash scripts/zlttbots-node.sh start
bash scripts/zlttbots-node.sh status
```

### Alternate runtime / edge tooling
Use Kubernetes, Cloudflare, and tunnel assets only when the incident environment actually depends on them. Do not apply a local-compose fix blindly to an edge or k8s environment.

## 9) Incident command sequence

Recommended order for severe incidents:
1. stabilize PostgreSQL and Redis
2. restore nginx or ingress reachability
3. restore predictor, crawler, arbitrage, and renderer baseline health
4. restore queue consumption and worker throughput
5. restore extended/internal services only after the baseline is stable
6. verify monitoring and logs
7. hand back to standard owners with evidence

## 10) Post-incident obligations

After recovery:
- record every command used
- capture exact timestamps and outcomes
- document root cause and containment
- update docs/runbooks if the incident exposed gaps
- identify whether the issue came from baseline runtime, extended Compose graph, Node-service layer, or edge/infrastructure drift
