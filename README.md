# zTTato Platform — Production Layout

This repository includes a production-ready Docker Compose deployment with isolated services, worker containers, reverse proxy routing, persistent state, and health checks.

## Production layout

```text
zttato-platform
│
├─ docker
│   ├─ postgres
│   └─ nginx
│
├─ services
│   ├─ viral-predictor
│   ├─ market-crawler
│   ├─ gpu-renderer
│   ├─ arbitrage-engine
│   ├─ analytics
│   ├─ click-tracker
│   └─ admin-panel
│
├─ workers
│   ├─ crawler-worker
│   ├─ arbitrage-worker
│   └─ renderer-worker
│
├─ infrastructure
│   ├─ postgres
│   │   └─ migrations
│   ├─ monitoring
│   └─ scripts
│
├─ configs
│   ├─ nginx.conf
│   └─ env
│
├─ docker-compose.yml
├─ .env
├─ start.sh
├─ stop.sh
└─ README.md
```


## Project status and recommended next additions

- Thai summary and implementation-ready roadmap: `docs/development/current-status-and-next-steps.md`
- Health endpoint catalog: `docs/operations/health-checks.md`
- Integration smoke test script: `scripts/test-integration.sh`

## Usage

```bash
./start.sh
```

Health status:

```bash
docker compose ps
```

Stop the stack:

```bash
./stop.sh
```

## Endpoints

- `http://SERVER/predict`
- `http://SERVER/crawl`
- `http://SERVER/arbitrage`

## Scale workers

```bash
docker compose up -d --scale crawler-worker=5
```

## Backup

```bash
pg_dump -U zttato zttato > backup.sql
```
