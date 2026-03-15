# Admin Manual

## 1. Purpose

This manual is for platform administrators responsible for account access, operational control, and business-level governance.

---

## 2. Admin Responsibilities

- Manage access to dashboard and role-scoped pages.
- Coordinate campaign execution and review operational metrics.
- Verify that core services and workers remain healthy.
- Route incidents to DevOps when infrastructure intervention is required.

---

## 3. Environment Startup and Shutdown

### Start platform

```bash
docker compose up -d
```

### Stop platform

```bash
docker compose down
```

### Check service state

```bash
docker compose ps
```

---

## 4. Service Inventory to Monitor

Administrators should recognize the core runtime set:

- `postgres`
- `redis`
- `viral-predictor`
- `market-crawler`
- `arbitrage-engine`
- `gpu-renderer`
- `crawler-worker`
- `arbitrage-worker`
- `renderer-worker`
- `nginx`

---

## 5. Operational Checks

### 5.1 Health Snapshot

```bash
docker compose ps
```

Confirm each critical service is `running` and healthy where health checks exist.

### 5.2 Logs

```bash
docker compose logs --tail=200 <service-name>
```

Use this to verify startup errors, queue stalls, or connectivity failures.

### 5.3 API Reachability

```bash
curl -i http://localhost/predict
curl -i http://localhost/crawl
curl -i http://localhost/arbitrage
```

A non-network error response still confirms routing works.

---

## 6. Worker Operations

Workers process background jobs and should be watched for throughput:

- `crawler-worker`
- `renderer-worker`
- `arbitrage-worker`

To scale workers when load increases:

```bash
docker compose up -d --scale crawler-worker=3 --scale renderer-worker=2 --scale arbitrage-worker=2
```

Adjust based on queue depth and resource limits.

---

## 7. Data Protection and Recovery

### Backup

```bash
pg_dump -U zttato zttato > backup.sql
```

### Restore

```bash
psql -U zttato zttato < backup.sql
```

Store backups securely with retention policy and access control.

---

## 8. Security Administration

- Enforce least privilege for platform users.
- Rotate credentials periodically (DB, app secrets, dashboard auth).
- Keep `.env` and secret files outside public sharing channels.
- Review unusual automation activity and account lockout patterns.

---

## 9. Incident Runbook (Admin Layer)

1. Detect issue from dashboard/API/alerts.
2. Confirm scope (single service or platform-wide).
3. Gather evidence (`docker compose ps`, logs, affected endpoints).
4. Apply safe restart if incident is transient.
5. Escalate with collected artifacts to DevOps for infra-level fixes.

---

## 10. Change Governance

- Document every production-affecting change.
- Prefer staged rollout for significant behavior updates.
- Validate critical flows after each deploy:
  - prediction
  - crawl
  - arbitrage
  - dashboard access
