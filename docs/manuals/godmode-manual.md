# Godmode Manual

## 1) Purpose and restrictions

Godmode is break-glass access for severe incidents, failed deployments, data-risk scenarios, or platform-wide recovery work. Use it only when standard admin or DevOps workflows are insufficient.

Rules:
- keep access tightly restricted
- make every action auditable
- record commands, timestamps, and intent
- prefer the smallest effective recovery action before escalating further

## 2) What godmode operators may control

A godmode operator may:
- rebuild and restart the default Compose stack
- control worker scale aggressively during incidents
- run recovery, repair, and diagnostics scripts from `scripts/` and `infrastructure/scripts/`
- manage monitoring, PostgreSQL, and optional Node-service lifecycle when required
- coordinate backup/restore and post-incident stabilization

## 3) Preconditions before acting

Before taking any action:
1. confirm the incident severity and scope
2. capture current state with `docker compose ps`, key logs, and active alerts
3. note whether PostgreSQL, Redis, gateway, or workers are implicated
4. define rollback or containment expectations
5. notify stakeholders if downtime or data risk is possible

## 4) Full-stack control operations

### Build and deploy baseline

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

### Verify post-action state

```bash
docker compose ps
```

## 5) High-pressure scaling actions

When backlog or incident load requires rapid worker increases:

```bash
docker compose up -d --scale crawler-worker=5 --scale renderer-worker=3 --scale arbitrage-worker=3
```

Guidance:
- scale in measured steps when possible
- inspect host CPU, memory, and container restart behavior after each step
- reverse the scale-up if saturation makes latency or errors worse

## 6) Recovery and diagnostics toolkit

Useful standard tools include:
- `scripts/test-integration.sh`
- `scripts/zttato-doctor.sh`
- `scripts/repair-platform.sh`
- `scripts/zttato-docker-recovery.sh`
- `scripts/fix-zttato-stack.sh`
- `infrastructure/scripts/validate-repo.sh`
- `infrastructure/scripts/rollback.sh`
- `infrastructure/scripts/bootstrap-platform.sh`

Prefer scripted recovery when available so the action is repeatable and easier to audit.

## 7) Data operations

### Backup

```bash
pg_dump -U zttato zttato > backup-$(date +%Y%m%d%H%M%S).sql
```

### Restore

```bash
psql -U zttato zttato < backup.sql
```

Before restoring:
- verify backup age and provenance
- reduce or stop write-heavy traffic
- decide whether a full-stack stop is needed
- prepare a post-restore validation checklist

## 8) Optional environment control paths

### Monitoring stack

```bash
docker compose -f infrastructure/monitoring/docker-compose.monitoring.yml up -d
```

### Node-service lifecycle

```bash
bash scripts/zttato-node.sh install
bash scripts/zttato-node.sh start
bash scripts/zttato-node.sh status
```

### Kubernetes / alternate deployment tooling
Use `infrastructure/k8s/`, Cloudflare assets, and deployment scripts only if the incident environment actually uses them. Do not assume the local Compose path and the Kubernetes path are interchangeable.

## 9) Incident command sequence

A practical order for severe incidents:
1. stabilize PostgreSQL and Redis
2. restore gateway reachability
3. restore predictor, crawler, arbitrage, and renderer APIs
4. restore worker consumption and queue movement
5. validate monitoring and logs
6. verify user-facing routes and critical workflows
7. hand off to standard ownership once stable

## 10) Post-incident obligations

After the platform is stable:
- record all commands used
- capture exact timestamps and outcomes
- summarize root cause and containment actions
- document any config drift discovered
- update runbooks and manuals if the incident exposed a documentation gap
