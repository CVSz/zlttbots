# Installation

This guide is the full-detail installer reference for zTTato Platform. It covers baseline setup, extended service expectations, optional Node-app setup, and common installation recovery paths.

## 1) Choose your installation path

### Path A — baseline local platform
Use this if you want the fastest reliable start for:

- PostgreSQL
- Redis
- virality scoring
- crawl queueing
- arbitrage review
- rendering queue intake
- nginx gateway

### Path B — full repository bootstrap
Use this if you want:

- baseline Compose services
- local dependency install across Python and Node service folders
- host-side bootstrap behavior from `start-zttato.sh`

### Path C — Node application fleet
Use this when you specifically need the admin panel or the separate Node services.

## 2) Prerequisites

### Required for baseline Compose
- Docker Engine
- Docker Compose plugin
- Git
- Python 3 with `pip` for running `pytest`

### Required for expanded local workflows
- Node.js and npm
- `curl`
- `psql` and `pg_dump` for database operations

### Optional but useful
- PM2 for Node-service lifecycle management
- `jq` for JSON inspection in shell workflows
- enough disk for multiple images and `node_modules`

### Recommended host baseline
- 4+ CPU cores
- 8+ GB RAM minimum
- 20+ GB free disk
- more memory if you plan to run the extended Compose/ML stack

## 3) Clone the repository

```bash
git clone <repository-url>
cd zttato-platform
```

## 4) Create the root `.env`

The main Compose file references `.env`, and several services rely on environment values for connectivity or external integration behavior.

### Recommended starter `.env`

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
DEFAULT_DAILY_SPEND_LIMIT=100.0
HTTP_TIMEOUT=10
RATE_TOKENS=60
RATE_MAX_TOKENS=120
RATE_REFILL_PER_SEC=1
```

### Important notes
- Leave `FFMPEG_HWACCEL=none` for CPU-only hosts.
- Change `AFFILIATE_WEBHOOK_SECRET` before any shared environment.
- Set `PLATFORM_API_BASE` and `PLATFORM_API_KEY` only if you plan to use `execution-engine` against a real partner endpoint.
- Never commit production credentials.

## 5) Validate your tooling

```bash
docker --version
docker compose version
python3 --version
pytest --version
```

Optional checks:

```bash
node --version
npm --version
pm2 -v
```

## 6) Build the platform images

### Standard build

```bash
docker compose build
```

### Troubleshooting build cache issues

```bash
docker compose build --no-cache
```

Use `--no-cache` only when you are intentionally diagnosing stale layers or dependency mismatch problems.

## 7) Start the platform

### Standard baseline startup

```bash
docker compose up -d
```

### Bootstrap helper startup

```bash
bash start.sh
```

This helper will create `.env` if needed, validate Compose config, and start the stack with build enabled.

### Full bootstrap script

```bash
bash start-zttato.sh
```

Use this only when you intentionally want the script to install Node dependencies, create Python virtual environments in service folders, bring up infrastructure, and attempt a broader host-assisted startup flow.

## 8) What starts in the default path

At minimum, expect the following baseline services to matter on day one:

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

Depending on the Compose invocation and available resources, additional control-plane services may also be started because they are declared in the main Compose file.

## 9) Verify service health

### Compose status

```bash
docker compose ps
```

### Gateway smoke checks

```bash
curl -i http://localhost/
curl -i -X POST http://localhost/predict -H 'content-type: application/json' -d '{"views":1000,"likes":100,"comments":10,"shares":5}'
curl -i -X POST http://localhost/crawl -H 'content-type: application/json' -d '{"keyword":"wireless earbuds"}'
curl -i http://localhost/arbitrage
```

### Direct service probes

```bash
curl -i http://localhost:9100/healthz || true
curl -i http://localhost:9300/healthz || true
curl -i http://localhost:9400/healthz || true
curl -i http://localhost:9500/healthz || true
```

Direct host access to those service ports only works if your environment publishes or forwards them. By default, nginx is the intended host entrypoint.

## 10) Run validation

```bash
pytest
bash scripts/test-integration.sh
bash infrastructure/scripts/validate-repo.sh
```

## 11) Optional Node-service installation

If you need the admin panel and other Node applications:

```bash
bash scripts/zttato-node.sh install
bash scripts/zttato-node.sh start
bash scripts/zttato-node.sh status
```

### Important note
This is a separate lifecycle from the nginx-routed Compose baseline. Treat it as an additional application layer, not a replacement for the Docker stack.

## 12) Optional monitoring installation

```bash
docker compose -f infrastructure/monitoring/docker-compose.monitoring.yml up -d
```

Expected local endpoints:
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`
- Loki: `http://localhost:3100`

## 13) Shutdown and cleanup

### Stop containers, keep data

```bash
docker compose down
```

### Stop and remove volumes

```bash
docker compose down -v
```

Do this only when you intentionally want to reset PostgreSQL/Redis local state.

## 14) Installation troubleshooting

### Compose config fails
- validate `.env` syntax
- run `docker compose config`
- confirm Docker daemon is running

### Containers exit repeatedly
- inspect `docker compose logs --tail=200 <service>`
- verify DB and Redis health first
- confirm host resource pressure is not causing restart loops

### Gateway is up but APIs fail
- verify nginx upstream routes in `configs/nginx.conf`
- inspect target service health checks
- confirm dependent stores are healthy

### Node-service wrapper fails
- verify Node and npm versions
- install PM2 if you need lifecycle management
- check per-service `package.json` scripts

### Full bootstrap script is too heavy
Use `bash start.sh` or direct `docker compose up -d` instead of `start-zttato.sh` for simpler local onboarding.
