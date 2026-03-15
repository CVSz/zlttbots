# Godmode Manual

## 1. Purpose and Scope

This manual defines high-authority operational control for trusted operators with full-platform permissions ("godmode").

Godmode access should be tightly limited, audited, and used only for emergency intervention, platform-wide migrations, or deep maintenance.

---

## 2. Godmode Capabilities

A godmode operator can:

- perform full-stack restart/rebuild
- scale workers and service replicas
- run repair and diagnostic scripts
- apply infrastructure and edge networking changes
- execute backup/restore procedures
- supervise incident response end-to-end

---

## 3. Preconditions Before Godmode Actions

1. Confirm incident severity and blast radius.
2. Snapshot current state (`docker compose ps`, key logs, active alerts).
3. Announce maintenance/incident handling to stakeholders.
4. Confirm rollback plan and data safety approach.

---

## 4. Full-Stack Control Commands

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

### Validate post-action health

```bash
docker compose ps
```

---

## 5. Worker and Throughput Control

Adjust worker capacity according to queue pressure and latency targets.

```bash
docker compose up -d --scale crawler-worker=5 --scale renderer-worker=3 --scale arbitrage-worker=3
```

Observe CPU/memory saturation and avoid over-scaling beyond host capacity.

---

## 6. Deep Diagnostics and Repair

Use repository scripts under `scripts/` for advanced troubleshooting, including:

- doctor and monitor scripts
- restart/supervisor scripts
- docker recovery and stack repair scripts
- cloudflare provisioning and tunnel recovery scripts

When possible, use scripted pathways instead of ad-hoc commands to keep operations repeatable.

---

## 7. Data and State Control

### Manual database backup

```bash
pg_dump -U zttato zttato > backup.sql
```

### Manual restore

```bash
psql -U zttato zttato < backup.sql
```

Before restore, ensure write operations are quiesced to prevent data divergence.

---

## 8. Edge and Network Override

Godmode may include control of Cloudflare and ingress automation:

- provisioning scripts
- DNS/tunnel creation scripts
- migration and heal scripts

Apply network changes incrementally and confirm service reachability after each step.

---

## 9. Incident Command Mode

During severe outages:

1. Stabilize data stores (`postgres`, `redis`).
2. Restore API baseline (`viral-predictor`, `market-crawler`, `arbitrage-engine`).
3. Restore workers and confirm queue movement.
4. Validate Nginx ingress and external routes.
5. Announce recovery status and residual risks.

---

## 10. Governance and Security Requirements

- Use godmode only with explicit approval in your organization.
- Maintain action logs and timestamps for postmortem.
- Separate personal and break-glass credentials.
- Rotate high-privilege secrets after major incidents.
- Perform post-incident review and convert ad-hoc fixes into documented runbooks.
