# Installation

This guide covers a practical local installation for development, smoke testing, and operator dry-runs.

## 1) Requirements

Minimum toolchain:

- Docker Engine + Docker Compose plugin
- Git
- Python 3 + `pip` (for tests)
- Optional: `psql` / `pg_dump` client tools (backup and restore operations)

Recommended host baseline:

- 4+ CPU cores
- 8+ GB RAM
- 20+ GB free disk for images/volumes

## 2) Clone repository

```bash
git clone <your-repository-url>
cd zttato-platform
```

## 3) Environment setup

If `.env` is required in your environment, create/populate it before startup.

Typical values include database and redis endpoints plus service tuning flags.

## 4) Build all services

```bash
docker compose build
```

If build fails:

- verify Docker daemon is running
- verify internet access for dependency pulls
- retry with `--no-cache` only when troubleshooting stale layers

## 5) Start stack

```bash
docker compose up -d
```

Expected critical services:

- `postgres`, `redis`
- `viral-predictor`, `market-crawler`, `arbitrage-engine`, `gpu-renderer`
- `crawler-worker`, `arbitrage-worker`, `renderer-worker`
- `nginx`

## 6) Verify runtime health

```bash
docker compose ps
```

Optionally inspect startup logs:

```bash
docker compose logs --tail=200
```

## 7) First API smoke checks

```bash
curl -i http://localhost/predict
curl -i http://localhost/crawl
curl -i http://localhost/arbitrage
```

A non-2xx response can still prove route reachability during initial smoke tests; focus first on transport/routing and service availability.

## 8) Run automated tests

```bash
pytest
```

## 9) Shutdown and cleanup

Stop containers while preserving data volumes:

```bash
docker compose down
```

Destroy volumes only when intentionally resetting local state:

```bash
docker compose down -v
```

## 10) Troubleshooting quick references

- Restart one service: `docker compose restart <service>`
- Recreate one service: `docker compose up -d --force-recreate <service>`
- Inspect a service log: `docker compose logs --tail=200 <service>`
- Inspect container-level status: `docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'`
