# zTTato Platform

zTTato Platform is a multi-service social-commerce and affiliate-operations workspace. The repository combines a runnable Docker Compose stack, a larger AI/automation control plane, operational shell tooling, enterprise-maturity reference modules, and an admin-panel UI for operators.

## Repository goals

The current repository supports four related usage modes:

1. **Baseline local platform** for product discovery, virality scoring, arbitrage review, rendering, PostgreSQL, Redis, and nginx.
2. **Expanded automation platform** with tenant onboarding, affiliate conversion intake, execution, market orchestration, billing, landing generation, and ML-oriented services defined in `docker-compose.yml`.
3. **Standalone Node application layer** for admin, analytics, click tracking, account automation, uploaders, miners, and marketplace helpers.
4. **Enterprise blueprint and validation layer** in `enterprise_maturity/` and `tests/` for service discovery, queueing, autoscaling, GPU scheduling, resilience, and governance patterns.

## What is in this repository

- **Compose runtime**: `docker-compose.yml` and root launcher scripts.
- **Services**: Python and Node services under `services/`.
- **Infrastructure assets**: PostgreSQL migrations, monitoring stack, Kubernetes manifests, Cloudflare helpers, CI, and bootstrap scripts.
- **Operational scripts**: install, deploy, repair, monitoring, and recovery utilities under `scripts/` and `infrastructure/scripts/`.
- **Documentation**: platform docs, manuals, API docs, runbooks, and development scan reports under `docs/`.

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

Or use helper workflows:

```bash
bash start.sh
bash scripts/start-zttato-platform.sh --core
bash scripts/zttato-manager.sh install
bash scripts/zttato-manager.sh status
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

## Documentation map

- System overview: `docs/system-overview.md`
- Installation: `docs/installation.md`
- Quick start: `docs/quick-start.md`
- Configuration: `docs/configuration.md`
- Manuals: `docs/manuals/`
- UI/UX guide: `docs/ux-ui/admin-panel-ux-ui.md`

## Security and support

- Security policy and reporting process: [`SECURITY.md`](SECURITY.md)
- Changelog and release history: [`CHANGELOG.md`](CHANGELOG.md)

## License

This repository is licensed under the MIT License. See [`LICENSE`](LICENSE) for details.
