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



## No-cost local stack (full source code)

This repository is fully source-available and can run end-to-end on a single machine with only open-source components (Docker, Postgres, Redis, Nginx, Python, Node).

- No paid cloud services are required for the default `docker compose` flow.
- GPU is optional: renderer now defaults to CPU encoding so you can run without NVIDIA hardware.
- If you have a GPU, set `FFMPEG_HWACCEL=cuda` in `.env` to enable NVENC.

Example `.env` overrides for free local mode:

```bash
FFMPEG_HWACCEL=none
FFMPEG_CPU_PRESET=veryfast
FFMPEG_CPU_CRF=23
```

## Full upgrade blueprint

The repository now ships a typed blueprint for a **full enterprise upgrade** that covers:

- 25+ microservices
- Kafka event system
- Distributed crawler cluster
- AI video generation pipeline
- Full admin dashboard modules
- Kubernetes namespaces
- CI/CD stages
- Full frontend app layout

See `enterprise_maturity/full_upgrade.py` and run the validation helper in tests.

A runnable reference implementation for the requested v3 capabilities is available in `enterprise_maturity/v3_runtime/`, including:

- API gateway + dynamic service discovery
- Central topic queue system
- Backlog-driven auto-scaling for workers
- GPU job scheduling
- Distributed crawler cluster manager

Run `pytest` to validate the runtime modules and integration behavior.

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
