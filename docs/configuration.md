# Configuration

This document summarizes how configuration works across the current zTTato repository, including the default Docker Compose stack, optional Node services, and supporting infrastructure assets.

## 1) Main configuration sources

### Compose runtime
- `.env` at the repository root for local Compose defaults.
- `docker-compose.yml` service `environment:` blocks for derived values like `DB_URL` and `REDIS_URL`.
- `configs/nginx.conf` for gateway routing.

### Supporting infrastructure
- `infrastructure/monitoring/docker-compose.monitoring.yml` for monitoring services.
- `infrastructure/postgres/docker-compose.postgres.yml` for standalone PostgreSQL setup.
- `infrastructure/k8s/` manifests for Kubernetes deployments, ingress, autoscaling, Kafka, JWT auth, and service mesh features.
- `infrastructure/cloudflare/*.tf` for Cloudflare-related infrastructure configuration.

### Service-local defaults
Several Python services read settings directly from environment variables at runtime, including database URLs, Redis URLs, and JWT-related values.

## 2) Core environment variables used by the Compose stack

### Database settings
- `DB_NAME` — PostgreSQL database name. Default: `zttato`
- `DB_USER` — PostgreSQL user. Default: `zttato`
- `DB_PASSWORD` — PostgreSQL password. Default: `zttato`
- `DB_PORT` — PostgreSQL port. Default: `5432`
- `DB_URL` — generated for some services from the variables above

### Redis settings
- `REDIS_HOST` — Redis hostname. Default: `redis`
- `REDIS_PORT` — Redis port. Default: `6379`
- `REDIS_URL` — generated for Redis-backed services from the variables above

### Renderer and FFmpeg settings
- `FFMPEG_HWACCEL` — hardware acceleration mode. Suggested values: `none`, `auto`, `cuda`
- `FFMPEG_CPU_PRESET` — CPU encoding preset, for example `veryfast`
- `FFMPEG_CPU_CRF` — CPU encoding quality factor, for example `23`

### General runtime variables you may still encounter
- `NODE_ENV` — Node.js runtime mode for standalone Node services
- `PYTHON_ENV` — Python runtime mode where used by deploy tooling
- `GPU_RENDER_ENABLED` — optional feature flag pattern referenced in documentation and deployment conventions

## 3) JWT auth service configuration

The `jwt-auth` service uses these variables when deployed:

- `JWT_ISSUER` — default `https://jwt-auth.platform.svc.cluster.local`
- `JWT_AUDIENCE` — default `zttato-platform`
- `JWT_SECRET` — signing secret; must be replaced in production
- `JWT_ALGORITHM` — default `HS256`
- `JWT_TTL_MINUTES` — token lifetime; default `30`

For any real environment, `JWT_SECRET` must be injected securely and never left at the default value.

## 4) Recommended local `.env`

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
NODE_ENV=development
PYTHON_ENV=development
```

## 5) Gateway configuration

Nginx currently exposes three proxied business routes and one root health endpoint:

- `/` — returns a simple text health response
- `/predict` — proxies to `viral-predictor:9100`
- `/crawl` — proxies to `market-crawler:9400`
- `/arbitrage` — proxies to `arbitrage-engine:9500`

The renderer API exists in the stack but is not currently proxied by Nginx in `configs/nginx.conf`; access it directly on its service port when needed in internal environments.

## 6) Database bootstrap behavior

On first startup, PostgreSQL loads SQL files from `infrastructure/postgres/migrations/` through `/docker-entrypoint-initdb.d`. The initial schema creates the core operational tables used by products, campaigns, videos, jobs, clicks, orders, and arbitrage records.

## 7) Monitoring configuration

The monitoring Compose file defines:
- Prometheus on port `9090`
- Grafana on port `3000`
- Loki on port `3100`
- Promtail reading Docker container logs

These monitoring services are not part of the default `docker compose up -d` baseline; start them explicitly when needed.

## 8) Configuration practices

- Keep secrets and production credentials out of source control.
- Use separate `.env` or secret injection methods for local, staging, and production environments.
- Replace all documented default credentials before any shared or production deployment.
- Prefer explicit variable names over hidden shell state in automation.
- Validate database and Redis connectivity during deployment acceptance.
- Document any environment-specific overrides close to the deployment artifact that uses them.

## 9) Production hardening checklist

Before deploying outside local development:
- change PostgreSQL defaults
- inject a strong `JWT_SECRET`
- restrict public ingress appropriately
- confirm whether renderer should use CPU or GPU
- enable monitoring and log collection
- review Kubernetes, Cloudflare, and service-mesh settings for the chosen environment
