# Quick Start

This guide gets a local zTTato environment running with the default Docker Compose stack.

## Prerequisites

- Docker Engine + Docker Compose
- Python 3 (for `pytest`)
- Git

## 1. Build

```bash
docker compose build
```

## 2. Start

```bash
docker compose up -d
```

## 3. Validate

```bash
docker compose ps
```

Expected critical runtime services include `postgres`, `redis`, API services, and workers (`crawler-worker`, `renderer-worker`, `arbitrage-worker`).

## 4. Run tests

```bash
pytest
```

## 5. Use the platform

- Dashboard (local): `http://localhost:5173`
- API routes (via nginx):
  - `http://localhost/predict`
  - `http://localhost/crawl`
  - `http://localhost/arbitrage`

## 6. Stop

```bash
docker compose down
```
