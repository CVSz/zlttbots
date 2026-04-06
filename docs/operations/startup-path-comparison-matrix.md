# Startup Path Comparison Matrix

This matrix keeps the **baseline runtime** and the **extended platform graph** explicitly separated for operations and onboarding.

| Path | Command | Primary Audience | Included Services | Excludes | Auth/Ownership Documentation Gate |
|---|---|---|---|---|---|
| Baseline runtime | `docker compose up -d nginx postgres redis viral-predictor market-crawler arbitrage-engine gpu-renderer tiktok-uploader analytics click-tracker account-farm ai-video-generator admin-panel` | Local development, smoke checks, day-one support | Core gateway, data stores, core crawler/render/predictor stack, admin panel | Tenant, billing, RL, model lifecycle, federation, scheduler, enterprise extras | Any newly exposed internal service must first have `docs/services/<service>.md` with auth mode + owner/team fields. |
| Extended platform graph | `docker compose up -d --build --remove-orphans` | Platform integration and full-system rehearsals | Full `docker-compose.yml` graph including tenant, billing, reward, model, RL, orchestration, and policy modules | N/A (superset of baseline) | Internal APIs remain non-public until auth, tenancy boundaries, and ownership are documented in `docs/services/` and reflected in `config/service-surface-manifest.json`. |
| Enterprise overlays | `docker compose -f docker-compose.enterprise.yml up -d` | Enterprise environment simulation | Additional enterprise services and overlays | Not intended for minimal local startup | Promotion requires documented ownership + auth controls in service docs and operations runbooks. |

## Canonical Admin Panel Runtime

The canonical admin-panel path is the **Next.js app-router implementation**. Do not reintroduce a parallel SPA runtime path; migrate SPA-only flows into the canonical Next.js service structure.
