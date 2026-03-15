# zTTato Platform

zTTato Platform is a multi-service automation stack for social-commerce operations, combining product discovery, AI scoring, rendering, campaign automation, and analytics in one deployable platform.

## What is in this repository

- **Microservices** in Node.js and Python under `services/`
- **Infrastructure** and orchestration assets under `infrastructure/`
- **Operational scripts** under `scripts/`
- **Platform documentation** under `docs/`

## Quick start

### 1) Build images

```bash
docker compose build
```

### 2) Start the stack

```bash
docker compose up -d
```

### 3) Verify runtime health

```bash
docker compose ps
```

### 4) Run tests

```bash
pytest
```

## Core workers

- `crawler-worker`
- `renderer-worker`
- `arbitrage-worker`

## Public API routes (via nginx)

- `http://localhost/predict`
- `http://localhost/crawl`
- `http://localhost/arbitrage`

## Common operations

### View logs

```bash
docker compose logs --tail=200 <service-name>
```

### Restart one service

```bash
docker compose restart <service-name>
```

### Scale workers

```bash
docker compose up -d --scale crawler-worker=3 --scale renderer-worker=2 --scale arbitrage-worker=2
```

## Documentation map

- Platform overview: `docs/system-overview.md`
- Installation: `docs/installation.md`
- Configuration: `docs/configuration.md`
- Project structure: `docs/project-structure.md`
- Quick start: `docs/quick-start.md`
- Manuals:
  - `docs/manuals/user-manual.md`
  - `docs/manuals/admin-manual.md`
  - `docs/manuals/devops-manual.md`
  - `docs/manuals/godmode-manual.md`

## License

Private internal infrastructure project.
