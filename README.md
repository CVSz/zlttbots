# zTTato Platform

zTTato Platform is an enterprise-focused AI + DevOps platform for social commerce, affiliate operations, and automation workloads. This repository combines runnable services, shared TypeScript packages, infrastructure assets, operational scripts, and deep technical documentation.

## Platform at a glance

- **Multi-service runtime**: Docker Compose stack for local development and service orchestration.
- **Application workspaces**: Node/TypeScript services in `apps/*` and shared contracts/types in `packages/*`.
- **Operational tooling**: lifecycle, bootstrap, deployment, repair, and diagnostics scripts in `scripts/` and `installer/`.
- **Infrastructure assets**: Terraform, Compose, and deployment support under `infra/` and `docs/infrastructure/`.
- **Reference architecture and audits**: enterprise maturity modules, runbooks, and security/operations reports in `docs/`.

## Repository layout

| Path | Purpose |
| --- | --- |
| `apps/` | API gateway, auth, billing, frontend, worker, and platform-core workspaces |
| `packages/` | Shared TypeScript definitions and reusable package code |
| `services/` | Additional platform services and runtime modules |
| `scripts/` | Install/start/stop/deploy/recovery automation scripts |
| `installer/` | Guided installation and bootstrap flows |
| `infra/` | Infrastructure artifacts (including Compose/Terraform) |
| `docs/` | Architecture, API docs, operations runbooks, installation manuals |
| `tests/` | Automated tests and validation assets |

## Quick start (local)

### 1. Prerequisites

- Docker 24+
- Docker Compose v2+
- Node.js 20+
- npm 10+
- Python 3.12+ (for Python service/tooling flows)

### 2. Configure environment

Create a `.env` file in the repository root:

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

### 3. Start core services

```bash
docker compose build
docker compose up -d
```

Alternative managed startup commands:

```bash
bash start.sh
bash scripts/start-zttato-platform.sh --core
bash scripts/zttato-manager.sh install
bash scripts/zttato-manager.sh status
```

### 4. Verify platform health

```bash
docker compose ps
curl -i http://localhost/
```

## Node workspace development

Install dependencies once:

```bash
npm install
```

Run all main workspace dev processes:

```bash
npm run dev
```

Build all workspaces:

```bash
npm run build
```

Run a specific workspace:

```bash
npm --workspace apps/frontend run dev
npm --workspace apps/api-gateway run dev
npm --workspace apps/platform-core run dev
```

## Common operations

### Logs

```bash
docker compose logs --tail=200 <service-name>
```

### Restart a service

```bash
docker compose restart <service-name>
```

### Scale workers

```bash
docker compose up -d --scale crawler-worker=3 --scale renderer-worker=2 --scale arbitrage-worker=2
```

### Run test suites

```bash
pytest
```

## Documentation index

- System overview: `docs/system-overview.md`
- Installation guide: `docs/installation.md`
- Quick-start guide: `docs/quick-start.md`
- Configuration reference: `docs/configuration.md`
- API documentation: `docs/api/`
- Operations runbooks: `docs/operations/runbooks/`
- Developer standards: `docs/development/coding-standards.md`

## Security and release information

- Security policy and reporting process: [`SECURITY.md`](SECURITY.md)
- Changelog and release history: [`CHANGELOG.md`](CHANGELOG.md)

## License

This repository is licensed under the MIT License. See [`LICENSE`](LICENSE) for details.
