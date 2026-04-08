# Full Source Code Metadata Snapshot (2026-04-08)

This document is a repository-wide metadata refresh for `zlttbots`, intended to provide a deterministic inventory of major source domains and runtime ownership.

## Snapshot metadata

- **Repository**: `zlttbots`
- **Snapshot date (UTC)**: `2026-04-08`
- **Snapshot scope**: full repository source tree (application code, scripts, infra assets, and tests)
- **Method**: static path inventory + top-level ownership mapping

## Top-level source domains

| Domain | Primary path(s) | Ownership focus | Runtime role |
| --- | --- | --- | --- |
| Application services | `apps/`, `services/` | Platform/application engineering | API, worker, orchestration, and business services |
| Shared libraries | `packages/`, `core/` | Shared platform engineering | Reusable contracts, types, and core logic |
| Infrastructure code | `infra/`, `infrastructure/`, `deploy/` | DevOps/SRE | Compose, Terraform, deployment automation |
| Automation scripts | `scripts/`, `installer/` | Platform operations | Install, bootstrap, lifecycle, diagnostics, remediation |
| Configuration | `config/`, `configs/`, `.env*` | Platform operations + security | Runtime and environment configuration |
| Documentation | `docs/`, `contracts/` | Architecture + platform governance | Technical specs, interface contracts, operational guidance |
| Quality gates | `tests/` | QA + engineering | Unit/integration/security/regression test suites |
| Edge/runtime workers | `workers/`, `cloudflare-devops/` | Edge platform engineering | Background processing and edge networking workflows |

## Source inventory checklist

The following checklist is intended for "full source code" change impact reviews:

1. **Application impact**
   - `apps/` and `services/` updated consistently.
   - Shared types/interfaces from `packages/` remain backward compatible.
2. **Operational impact**
   - `scripts/`, `installer/`, and runtime entrypoints still support idempotent execution.
   - `infra/` and `infrastructure/` assets remain aligned with service topology.
3. **Security impact**
   - No credentials committed in plaintext.
   - Existing auth/validation/rate-limiting expectations are preserved.
4. **Test impact**
   - `tests/` coverage updated where behavior changes.
   - Smoke/integration checks still pass in CI.
5. **Documentation impact**
   - `docs/` and `contracts/` updated to reflect behavior/config changes.

## Deterministic review command set

Use these commands for repeatable metadata validation:

```bash
rg --files
rg --files apps services packages core scripts installer infra infrastructure deploy config configs tests workers cloudflare-devops
pytest -q
```

## Notes

- This metadata snapshot is intentionally path-oriented and deterministic.
- For deeper architecture context, pair this file with:
  - `docs/system-overview.md`
  - `docs/project-structure.md`
  - `docs/development/current-status-and-next-steps.md`
