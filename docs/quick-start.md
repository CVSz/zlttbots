# Quick Start

Use this guide for the fastest reliable path to a working local zTTato baseline.

## Prerequisites

- Docker Engine
- Docker Compose plugin
- Python 3
- Git
- A repository-root `.env` file

## 1) Create a minimal `.env`

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

## 2) Build images

```bash
docker compose build
```

## 3) Start the platform

```bash
docker compose up -d
```

## 4) Check service state

```bash
docker compose ps
```

Expected baseline services:
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

## 5) Verify the gateway and APIs

### Root health

```bash
curl -i http://localhost/
```

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

## 6) Run tests

```bash
pytest
```

## 7) Useful daily commands

### Tail logs for one service

```bash
docker compose logs --tail=200 market-crawler
```

### Restart one service

```bash
docker compose restart market-crawler
```

### Scale workers

```bash
docker compose up -d --scale crawler-worker=3 --scale renderer-worker=2 --scale arbitrage-worker=2
```

## 8) Optional extras

### Start standalone Node services

```bash
bash scripts/zttato-node.sh install
bash scripts/zttato-node.sh start
bash scripts/zttato-node.sh status
```

### Start monitoring stack

```bash
docker compose -f infrastructure/monitoring/docker-compose.monitoring.yml up -d
```

## 9) Stop the environment

```bash
docker compose down
```
