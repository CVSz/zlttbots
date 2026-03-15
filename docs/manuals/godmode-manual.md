# Godmode Manual

## 1. Purpose and restrictions

Godmode access is break-glass operational control for severe incidents, platform-wide maintenance, or recovery scenarios. Access must be tightly restricted and auditable.

## 2. Capabilities

A godmode operator may:

- run full stack restart/rebuild actions
- scale workers and service capacity
- execute repair, recovery, and infrastructure scripts
- perform backup and restore operations
- lead incident command from detection to recovery

## 3. Preconditions before action

1. Confirm severity and blast radius.
2. Capture initial state (`docker compose ps`, key logs, active alerts).
3. Communicate maintenance/incident window.
4. Confirm rollback and data-protection plan.

## 4. Full-stack control

### Build and deploy

```bash
docker compose build
docker compose up -d
```

### Controlled restart

```bash
docker compose down
docker compose up -d
```

### Emergency stop

```bash
docker compose down
```

### Post-action verification

```bash
docker compose ps
```

## 5. Throughput control

```bash
docker compose up -d --scale crawler-worker=5 --scale renderer-worker=3 --scale arbitrage-worker=3
```

Scale incrementally and monitor host saturation.

## 6. Recovery and diagnostics

Prefer standard scripts in `scripts/` and `infrastructure/scripts/` for repeatability (doctor, monitor, repair, rollback, deploy).

## 7. Data state operations

### Backup

```bash
pg_dump -U zttato zttato > backup-$(date +%Y%m%d%H%M%S).sql
```

### Restore

```bash
psql -U zttato zttato < backup.sql
```

Quiesce write-heavy operations before restore.

## 8. Incident command sequence

1. Stabilize data stores.
2. Restore API baseline.
3. Restore workers and queue movement.
4. Validate ingress and external routes.
5. Publish recovery state and residual risks.
