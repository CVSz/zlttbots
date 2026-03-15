# Installation

This document covers local setup for development and operational testing.

## Requirements

- Docker + Docker Compose
- Python 3 and `pip`
- Git
- Optional: `psql`/`pg_dump` client tools for backup/restore workflows

## Clone

```bash
git clone <your-repository-url>
cd zttato-platform
```

## Build and start

```bash
docker compose build
docker compose up -d
```

## Verify stack

```bash
docker compose ps
```

## Run tests

```bash
pytest
```

## First health checks

```bash
curl -i http://localhost/predict
curl -i http://localhost/crawl
curl -i http://localhost/arbitrage
```

## Stop and clean down

```bash
docker compose down
```

Use `docker compose down -v` only when you intentionally want to remove persisted volumes.
