# Quick Start

Use this guide when you want a fast, repeatable local bootstrap in a few commands.

## Prerequisites

- Docker Engine + Docker Compose
- Git
- Python 3 (for test execution)

## 1) Build images

```bash
docker compose build
```

## 2) Start the platform

```bash
docker compose up -d
```

## 3) Check service status

```bash
docker compose ps
```

Target state: core services are `Up` and health checks are green (or transitioning to healthy during warm-up).

## 4) Validate key API routes

```bash
curl -i http://localhost/predict
curl -i http://localhost/crawl
curl -i http://localhost/arbitrage
```

## 5) Run tests

```bash
pytest
```

## 6) Daily operations shortcuts

- Tail logs for one service:
  ```bash
  docker compose logs --tail=200 market-crawler
  ```
- Restart one service:
  ```bash
  docker compose restart market-crawler
  ```
- Scale worker throughput:
  ```bash
  docker compose up -d --scale crawler-worker=3 --scale renderer-worker=2 --scale arbitrage-worker=2
  ```

## 7) Access points

- API gateway (nginx): `http://localhost`
  - Predict route: `/predict`
  - Crawl route: `/crawl`
  - Arbitrage route: `/arbitrage`
- Admin panel is available from the repository under `services/admin-panel` for frontend runtime workflows.

## 8) Stop the environment

```bash
docker compose down
```
