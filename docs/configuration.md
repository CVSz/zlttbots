# Configuration

This document is the full configuration reference for the current zTTato repository. It focuses on the active local stack, the most relevant extended Compose variables, the Node-service layer, and practical configuration guidance.

## 1) Main configuration sources

### Root runtime files
- `.env` — primary source for Compose-local environment values
- `docker compose.yml` — service wiring, dependency graph, build contexts, health checks, environment propagation
- `configs/nginx.conf` — gateway routes exposed on port `80`
- `configs/env/production.env` — template/default source used by bootstrap flows when `.env` is missing

### Infrastructure config
- `infrastructure/postgres/migrations/` — bootstrap SQL schema
- `infrastructure/monitoring/*.yml` — Prometheus/Grafana/Loki/Promtail config
- `infrastructure/k8s/` — Kubernetes manifests and related environment assumptions
- `infrastructure/cloudflare/` — Cloudflare infrastructure configuration

### App/service-local config
- `package.json` / framework configs in Node services
- Python service defaults in each service entrypoint module (commonly `src/main.py`) or supporting module
- PM2-oriented wrapper scripts under `scripts/`

## 2) Core baseline environment variables

### Database
- `DB_NAME` — default `zttato`
- `DB_USER` — default `zttato`
- `DB_PASSWORD` — default `zttato`
- `DB_PORT` — default `5432`

Compose derives PostgreSQL URLs such as:

```text
postgresql://${DB_USER}:${DB_PASSWORD}@postgres:${DB_PORT}/${DB_NAME}
```

### Redis
- `REDIS_HOST` — default `redis`
- `REDIS_PORT` — default `6379`

Compose derives Redis URLs such as:

```text
redis://${REDIS_HOST}:${REDIS_PORT}
```

### FFmpeg / renderer behavior
- `FFMPEG_HWACCEL` — use `none` for CPU-only local setups; other documented values include `auto` and `cuda`
- `FFMPEG_CPU_PRESET` — CPU encoder preset, for example `veryfast`
- `FFMPEG_CPU_CRF` — quality/compression tradeoff value, for example `23`

## 3) Extended Compose variables worth knowing

### Execution engine
- `PLATFORM_API_BASE` — upstream partner API base URL
- `PLATFORM_API_KEY` — bearer token used for outbound publish/status calls
- `HTTP_TIMEOUT` — request timeout for upstream calls
- `RATE_TOKENS` — current token bucket size
- `RATE_MAX_TOKENS` — maximum token bucket size
- `RATE_REFILL_PER_SEC` — token refill speed

### Affiliate webhook
- `AFFILIATE_WEBHOOK_SECRET` — HMAC secret for verifying `X-Signature`
- `REWARD_COLLECTOR_URL` — internal target for normalized reward forwarding
- `DATABASE_URL` — database connection URL when running the service outside root Compose defaults

### Tenant service
- `DEFAULT_DAILY_SPEND_LIMIT` — default spend ceiling applied when creating tenants
- `DATABASE_URL` — tenant persistence connection string

### JWT auth service when deployed separately
- `JWT_ISSUER`
- `JWT_AUDIENCE`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `JWT_TTL_MINUTES`

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
PLATFORM_API_BASE=https://api.partner.example
PLATFORM_API_KEY=
AFFILIATE_WEBHOOK_SECRET=change-me
DEFAULT_DAILY_SPEND_LIMIT=100.0
HTTP_TIMEOUT=10
RATE_TOKENS=60
RATE_MAX_TOKENS=120
RATE_REFILL_PER_SEC=1
NODE_ENV=development
PYTHON_ENV=development
```

## 5) Gateway configuration

Nginx currently defines the following upstreams and routes:

- upstream `predictor` → `viral-predictor:9100`
- upstream `crawler` → `market-crawler:9400`
- upstream `arbitrage` → `arbitrage-engine:9500`

Host routes:
- `/` — text health response
- `/predict` — predictor proxy
- `/crawl` — crawler proxy
- `/arbitrage` — arbitrage proxy

### Important limitation
`gpu-renderer`, `tenant-service`, `execution-engine`, `affiliate-webhook`, and the other extended services are **not** routed through nginx in the default config. If you need them publicly, add ingress explicitly and document the security model.

## 6) Service dependency shape in Compose

### Database-backed services
Examples:
- `viral-predictor`
- `arbitrage-engine`
- `tenant-service`
- `affiliate-webhook`
- `federation`

### Redis-backed services
Examples:
- `market-crawler`
- `gpu-renderer`
- `feature-store`
- parts of the RL/model-serving stack

### Redpanda-backed/event-stream services
Examples:
- `reward-collector`
- `stream-consumer`
- `rl-trainer`
- `model-service`
- `master-orchestrator`

## 7) Bootstrap behavior to be aware of

### `start.sh`
- creates `.env` when missing
- validates Compose config
- runs `docker compose up -d --build --remove-orphans`

### `start-zttato.sh`
- makes shell scripts executable
- sources `infrastructure/start/env.sh`
- installs Node dependencies across services
- creates Python virtual environments in service folders and installs requirements
- starts base infrastructure
- builds and starts Compose services
- optionally runs host-side local worker helpers

This makes `start-zttato.sh` more powerful but also heavier and more invasive than `start.sh`.

## 8) Node-service configuration path

Node services use their own package/runtime configs. Operational wrapper entrypoint:

```bash
bash scripts/zttato-node.sh {install|start|stop|restart|status|logs}
```

If you enable that path, document:
- which services are expected to run
- which ports they bind to
- whether PM2 is installed
- where logs are stored

## 9) Configuration practices

- Never commit production secrets.
- Replace all placeholder/default credentials before any shared deployment.
- Keep the gateway exposure list deliberately small.
- Treat internal-only services as internal until authentication and routing are defined.
- Document environment-specific overrides close to the deployment artifact that uses them.
- Validate Compose config after changing `.env`, nginx, or service dependencies.

## 10) Production hardening checklist

Before real deployment outside local development:
- change PostgreSQL defaults
- set strong webhook/JWT secrets
- define which internal services will be exposed and through what auth layer
- confirm renderer CPU/GPU mode intentionally
- enable monitoring and centralized logging
- review Cloudflare, Kubernetes, and mesh configs for parity with actual runtime

## 11) Interactive domain env generator (`*.zeaz.dev`)

To generate a domain env file that maps the standard edge services under one base domain (for example `*.zeaz.dev`), run:

```bash
bash scripts/generate-domain-env.sh
```

You can also run non-interactively:

```bash
bash scripts/generate-domain-env.sh --domain zeaz.dev --output configs/env/domain.env --yes
```

Generated keys include:
- `WILDCARD_DOMAIN=*.{domain}`
- `API_BASE_URL=https://api.{domain}`
- `ADMIN_BASE_URL=https://admin.{domain}`
- `AUTH_BASE_URL=https://auth.{domain}`
- `AI_BASE_URL=https://ai.{domain}`
- `CRAWL_BASE_URL=https://crawl.{domain}`
- `PREDICT_BASE_URL=https://predict.{domain}`
- `GRAFANA_BASE_URL=https://grafana.{domain}`
- `KAFKA_BASE_URL=https://kafka.{domain}`
