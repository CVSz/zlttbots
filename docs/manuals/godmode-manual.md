# Godmode Manual

## 1. Purpose and restrictions

Godmode access is break-glass control intended for severe incidents, platform-wide maintenance, or high-risk recovery operations.

Rules:

- Access must be tightly restricted.
- Every action must be auditable.
- Use only when standard operator/admin authority is insufficient.

## 2. Godmode capabilities

A godmode operator may:

- execute full stack rebuild/restart procedures
- scale workers and service capacity rapidly
- run advanced diagnostics, repair, and recovery scripts
- perform backup/restore and controlled recovery sequencing
- lead incident command until stabilization

## 3. Preconditions before any action

1. Confirm severity and blast radius.
2. Capture initial state (`docker compose ps`, key logs, active alerts).
3. Announce maintenance/incident command window.
4. Confirm rollback and data-protection plan.

## 4. Full-stack control operations

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

### Verification

```bash
docker compose ps
```

## 5. Throughput and pressure control

```bash
docker compose up -d --scale crawler-worker=5 --scale renderer-worker=3 --scale arbitrage-worker=3
```

Guidance:

- Scale in measured increments.
- Observe host saturation before each scale-up step.
- Revert scaling if resource contention worsens latency/error rates.

## 6. Recovery and diagnostics toolkit

Prefer standardized scripts for repeatability:

- `scripts/` (doctor, monitor, repair, restart, deploy helpers)
- `infrastructure/scripts/` (bootstrap, rollback, validation, build tooling)

Use script output as incident evidence artifacts.

## 7. Data operations and integrity

### Backup

```bash
pg_dump -U zttato zttato > backup-$(date +%Y%m%d%H%M%S).sql
```

### Restore

```bash
psql -U zttato zttato < backup.sql
```

Before restore:

- Quiesce write-heavy services where possible.
- Verify backup age and integrity.
- Define clear post-restore validation checklist.

## 8. Incident command sequence

1. Stabilize data stores.
2. Restore API baseline.
3. Restore workers and queue movement.
4. Validate ingress and external routes.
5. Publish recovery status and residual risk.

## 9. Post-incident obligations

- Record all commands and timestamps.
- Document root cause and containment decisions.
- Propose preventive controls and runbook updates.
- Hand off to standard ownership once stable.
