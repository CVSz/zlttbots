# zTTato Platform

zTTato Platform is a multi-service social-commerce and affiliate-operations workspace. The repository combines a runnable Docker Compose stack, a larger AI/automation control plane, operational shell tooling, enterprise-maturity reference modules, and an admin-panel UI for operators.

## Repository goals

The current repository supports four different but related usage modes:

1. **Baseline local platform** for product discovery, virality scoring, arbitrage review, rendering, PostgreSQL, Redis, and nginx.
2. **Expanded automation platform** with tenant onboarding, affiliate conversion intake, execution, market orchestration, billing, landing generation, feature-store and RL-oriented services defined in `docker-compose.yml`.
3. **Standalone Node application layer** for admin, analytics, click tracking, account automation, uploaders, miners, and marketplace helpers run separately from the default Compose flow.
4. **Enterprise blueprint and validation layer** in `enterprise_maturity/` and `tests/` for service discovery, queueing, autoscaling, GPU scheduling, resilience, and governance patterns.

## What is in this repository

- **Compose runtime**: `docker-compose.yml` and root launcher scripts.
- **Services**: Python and Node services under `services/`.
- **Infrastructure assets**: PostgreSQL migrations, monitoring stack, Kubernetes manifests, Cloudflare helpers, CI and bootstrap scripts.
- **Operational scripts**: install, deploy, repair, monitoring, and recovery utilities under `scripts/` and `infrastructure/scripts/`.
- **Documentation**: platform docs, manuals, API docs, runbooks, and development scan reports under `docs/`.

## Runtime layers at a glance

### 1) Baseline gateway surface
The nginx layer currently publishes the following host routes on `http://localhost`:

- `GET /` → gateway health string
- `POST /predict` → `viral-predictor`
- `POST /crawl` → `market-crawler`
- `GET /arbitrage` → `arbitrage-engine`

### 2) Core baseline services
The baseline stack used most often for local work includes:

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

### 3) Extended control-plane services already declared in Compose
The main Compose file also defines additional services for broader platform scenarios, including:

- tenant onboarding: `tenant-service`
- partner callback intake: `affiliate-webhook`
- content publishing bridge: `execution-engine`
- commerce launch flow: `product-generator`, `market-orchestrator`, `billing-service`, `landing-service`
- reward and event pipeline: `reward-collector`, `redpanda`, `stream-consumer`
- AI/ML platform: `feature-store`, `model-service`, `model-registry`, `model-sync`, `drift-detector`, `retraining-loop`
- RL stack: `rl-trainer`, `rl-coordinator`, `rl-engine`, `rl-agent-1`, `rl-agent-2`, `rl-policy`
- optimization/orchestration: `budget-allocator`, `rtb-engine`, `scaling-engine`, `master-orchestrator`, `scheduler`, `capital-allocator`, `federation`
- distributed runtime helpers: `ray-head`, `ray-worker`, `p2p-node`

Not every one of these services is exposed through nginx, and not every one is intended for first-day local use. The documentation below explains the safe entry paths.

## Fastest start

### 1) Create `.env`

```env
DB_NAME=zttato
DB_USER=zttato
DB_PASSWORD=zttato
DB_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6379
FFMPEG_HWACCEL=none
FFMPEG_CPU_PRESET=veryfast
FFMPEG_CPU_CRF=23
PLATFORM_API_BASE=https://api.partner.example
PLATFORM_API_KEY=
AFFILIATE_WEBHOOK_SECRET=change-me
```

### 2) Build and start

```bash
docker compose build
docker compose up -d
```

Or use the repository bootstrap helper:

```bash
bash start.sh
```

Or use the new platform manager flows:

```bash
bash scripts/zttato-manager.sh install
bash scripts/zttato-manager.sh upgrade
bash scripts/zttato-manager.sh deploy
```

### 3) Verify health

```bash
docker compose ps
curl -i http://localhost/
```

### 4) Run tests

```bash
pytest
```

## Common operations

### View logs

```bash
docker compose logs --tail=200 <service-name>
```

### Restart one service

```bash
docker compose restart <service-name>
```

### Scale worker replicas

```bash
docker compose up -d --scale crawler-worker=3 --scale renderer-worker=2 --scale arbitrage-worker=2
```

### Use the zTTato manager

```bash
bash scripts/zttato-manager.sh status
bash scripts/zttato-manager.sh logs nginx
```

### Use the Node-service wrapper

```bash
bash scripts/zttato-node.sh install
bash scripts/zttato-node.sh start
bash scripts/zttato-node.sh status
```

## Documentation map

### Platform docs
- System overview: `docs/system-overview.md`
- Project structure: `docs/project-structure.md`
- Installation: `docs/installation.md`
- Quick start: `docs/quick-start.md`
- Configuration: `docs/configuration.md`

### Manuals
- User manual: `docs/manuals/user-manual.md`
- Admin manual: `docs/manuals/admin-manual.md`
- DevOps manual: `docs/manuals/devops-manual.md`
- Godmode manual: `docs/manuals/godmode-manual.md`

### UI / UX
- Admin panel service detail: `docs/services/admin-panel.md`
- Admin panel UX/UI guide: `docs/ux-ui/admin-panel-ux-ui.md`

### Development scan reports
- Repository scan (2026-03-21): `docs/development/full-source-scan-report-2026-03-21.md`

## Recommended reading order

If you are new to the repository, read in this order:

1. `README.md`
2. `docs/system-overview.md`
3. `docs/installation.md`
4. `docs/quick-start.md`
5. `docs/configuration.md`
6. the manual for your role
7. the service or UI doc for the component you are touching

## License

Private internal infrastructure project.
