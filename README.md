# zttato-platform

A multi-service growth/automation platform with Node.js and Python services, Docker-based infrastructure, Kubernetes manifests, and Cloudflare edge automation scripts.

## Repository Overview

```text
.
├── docker-compose.yml                # Core local stack (postgres, redis, core python APIs)
├── start-zttato.sh                   # Unified bootstrap script
├── env.edge                          # Edge-related env sample
├── cloudflare-devops/                # Cloudflare tunnel + DNS helper toolkit
├── infrastructure/
│   ├── ci/                           # Build/deploy helper scripts
│   ├── k8s/                          # Kubernetes deployments/services/ingress/config
│   ├── postgres/                     # Postgres config + migrations
│   ├── scripts/                      # Platform operations scripts
│   └── start/                        # Env and worker startup scripts
├── scripts/                          # Additional operational/fix/deploy scripts
└── services/
    ├── account-farm/                 # Account automation service (Node)
    ├── admin-panel/                  # Frontend dashboard (React)
    ├── ai-video-generator/           # AI video generation pipeline (Node)
    ├── analytics/                    # Analytics API/metrics (Node)
    ├── arbitrage-engine/             # Arbitrage API/worker (Python)
    ├── click-tracker/                # Click/fingerprint tracking (Node)
    ├── gpu-renderer/                 # Render queue + API (Python)
    ├── market-crawler/               # Market crawler API/workers (Python)
    ├── shopee-crawler/               # Shopee crawler (Node)
    ├── tiktok-farm/                  # TikTok farm scheduler/uploader (Node)
    ├── tiktok-shop-miner/            # TikTok shop mining service (Node)
    └── viral-predictor/              # ML prediction API/training (Python)
```

## Current Validation Status

Validation checks performed in this repository:

- Shell syntax check across all `*.sh` scripts.
- Python syntax byte-compile for all `*.py` files.
- JSON parse check for all `package.json` files.

### Result

- ✅ Repository is now syntactically valid for shell/python/json checks.
- 🔧 Fixed one blocking shell syntax issue in:
  - `scripts/generate-cloudflare-devops-toolkit-v2.sh`
  - Missing closing quote in `chmod +x "$TOOLKIT/install.sh"`.

## Local Run (quick start)

### 1) Prerequisites

- Docker + Docker Compose
- Node.js + npm
- Python 3 + venv

### 2) Bootstrap

```bash
bash start-zttato.sh
```

This script:
- makes scripts executable,
- installs service dependencies,
- starts postgres/redis,
- builds/starts compose services,
- applies SQL migrations,
- starts worker scripts,
- runs basic health checks.

## Manual Checks

```bash
# Shell syntax
while IFS= read -r f; do bash -n "$f"; done < <(rg --files -g '*.sh')

# Python syntax
python -m compileall services

# package.json validity
while IFS= read -r f; do python -m json.tool "$f" >/dev/null; done < <(rg --files -g 'package.json')
```

## Notes

- Docker runtime checks (such as `docker compose config`) require Docker CLI in the environment.
- Cloudflare scripts require a valid API token/account/zone configuration.
