# Installation

This guide covers the current repository from the simplest local Compose install through optional Node service setup and supporting infrastructure.

## 1) Prerequisites

### Required for the default stack
- Docker Engine
- Docker Compose plugin
- Git
- Python 3.x and `pip` for running `pytest`

### Optional, depending on what you want to run
- Node.js and npm for standalone services under `services/`
- PM2 for PM2-managed Node service startup via `scripts/zttato-node.sh`
- `curl` for smoke checks
- `psql` and `pg_dump` for backup/restore workflows

### Recommended host baseline
- 4+ CPU cores
- 8+ GB RAM
- 20+ GB free disk for images, node modules, and database volumes

## 2) Clone the repository

```bash
git clone <repository-url>
cd zttato-platform
```

## 3) Create environment configuration

The Compose file references `.env`. Create one before starting the stack.

### Minimal `.env` example

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
```

### Notes
- `FFMPEG_HWACCEL=none` is the safest default for CPU-only local environments.
- Set `FFMPEG_HWACCEL=cuda` only when your host and container runtime are prepared for NVIDIA acceleration.
- Add any service-specific secrets to `.env`, but do not commit them.

## 4) Build the Compose stack

```bash
docker compose build
```

If the build fails:
- confirm the Docker daemon is running
- confirm network access for base image and dependency pulls
- retry with `--no-cache` only when troubleshooting stale layers

## 5) Start the baseline platform

```bash
docker compose up -d
```

This brings up:
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

## 6) Verify container health

```bash
docker compose ps
```

You should see the data services, API services, workers, and Nginx all in a running state. For deeper detail:

```bash
docker compose logs --tail=200
```

## 7) Run first smoke checks

### Root gateway probe

```bash
curl -i http://localhost/
```

### Predictor smoke check

```bash
curl -i -X POST http://localhost/predict \
  -H 'content-type: application/json' \
  -d '{"views":1000,"likes":100,"comments":10,"shares":5}'
```

### Crawler smoke check

```bash
curl -i -X POST http://localhost/crawl \
  -H 'content-type: application/json' \
  -d '{"keyword":"wireless earbuds"}'
```

### Arbitrage smoke check

```bash
curl -i http://localhost/arbitrage
```

## 8) Run the test suite

```bash
pytest
```

The repository test suite validates the runtime blueprint, GPU render command behavior, JWT auth behavior, and enterprise maturity support.

## 9) Optional: install and run standalone Node services

Use this path only if you need the extra Node applications in `services/`.

### Install dependencies

```bash
bash scripts/zttato-node.sh install
```

### Start PM2-managed Node services

```bash
bash scripts/zttato-node.sh start
```

### Check PM2 status

```bash
bash scripts/zttato-node.sh status
```

### View logs

```bash
bash scripts/zttato-node.sh logs
bash scripts/zttato-node.sh logs admin-panel
```

## 10) Optional: monitoring stack

Start the monitoring stack separately if you want Prometheus/Grafana/Loki locally.

```bash
docker compose -f infrastructure/monitoring/docker-compose.monitoring.yml up -d
```

Endpoints:
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`
- Loki: `http://localhost:3100`

## 11) Shutdown and cleanup

### Stop containers, keep data

```bash
docker compose down
```

### Stop containers and remove volumes

```bash
docker compose down -v
```

Use volume removal only when you intentionally want to reset local PostgreSQL and Redis state.

## 12) Troubleshooting quick reference

- Restart one service:
  ```bash
  docker compose restart <service>
  ```
- Recreate one service:
  ```bash
  docker compose up -d --force-recreate <service>
  ```
- Inspect one service log:
  ```bash
  docker compose logs --tail=200 <service>
  ```
- Check direct container status:
  ```bash
  docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
  ```
- Run the included integration smoke script:
  ```bash
  bash scripts/test-integration.sh
  ```
