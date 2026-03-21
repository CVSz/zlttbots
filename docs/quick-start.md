# Quick Start

This is the full starter-platform guide for getting zTTato running fast without reading the entire repository first.

## Goal

Start the platform, verify the gateway, run one request per core API, and know where to go next.

## 1) Create `.env`

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

## 2) Build images

```bash
docker compose build
```

## 3) Start the stack

```bash
docker compose up -d
```

If you prefer the helper script:

```bash
bash start.sh
```

## 4) Check container state

```bash
docker compose ps
```

Focus first on these services:
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

## 5) Verify the gateway

### Root health

```bash
curl -i http://localhost/
```

Expected behavior: a `200` response with the gateway health string.

## 6) Exercise the baseline APIs

### Predictor

```bash
curl -i -X POST http://localhost/predict \
  -H 'content-type: application/json' \
  -d '{"views":1000,"likes":100,"comments":10,"shares":5}'
```

### Crawler

```bash
curl -i -X POST http://localhost/crawl \
  -H 'content-type: application/json' \
  -d '{"keyword":"wireless earbuds"}'
```

### Arbitrage

```bash
curl -i http://localhost/arbitrage
```

## 7) Know what those calls do

- `/predict` returns a virality score.
- `/crawl` queues a crawl job for background worker processing.
- `/arbitrage` returns the top arbitrage rows currently available in PostgreSQL.
- `/render` exists on the internal renderer service but is not routed publicly by nginx by default.

## 8) Run repository validation

```bash
pytest
```

Optional additional checks:

```bash
bash scripts/test-integration.sh
bash infrastructure/scripts/validate-repo.sh
```

## 9) Useful day-two commands

### View logs

```bash
docker compose logs --tail=200 market-crawler
docker compose logs --tail=200 nginx
```

### Restart one service

```bash
docker compose restart market-crawler
```

### Scale workers

```bash
docker compose up -d --scale crawler-worker=3 --scale renderer-worker=2 --scale arbitrage-worker=2
```

## 10) Optional next steps

### Run the Node application layer

```bash
bash scripts/zttato-node.sh install
bash scripts/zttato-node.sh start
```

### Start the monitoring stack

```bash
docker compose -f infrastructure/monitoring/docker-compose.monitoring.yml up -d
```

### Read deeper docs
- installer reference: `docs/installation.md`
- configuration reference: `docs/configuration.md`
- role manuals: `docs/manuals/`
- admin UI docs: `docs/services/admin-panel.md` and `docs/ux-ui/admin-panel-ux-ui.md`

## 11) Stop the environment

```bash
docker compose down
```
