# Full Source Scan Report (2026-03-21)

## Scope

This report summarizes a fresh repository scan focused on the current structure, runtime topology, documentation alignment, and available validation commands.

## What was scanned

- repository-wide file inventory
- documentation tree and manuals
- root Compose topology
- bootstrap scripts
- gateway config
- baseline Python API entrypoints
- selected extended Compose services
- admin-panel UI source structure

## High-level findings

1. **The repository is larger than the original “baseline stack” story.**
   The main Compose file now defines a baseline runtime plus a wider control-plane service graph for tenant, affiliate, reward, feature-store, model, RL, orchestration, and distributed-runtime concerns.
2. **The safest operational story is still baseline-first.**
   Nginx publicly exposes only `/`, `/predict`, `/crawl`, and `/arbitrage`, so those remain the clearest supported entrypoints.
3. **The admin-panel service contains two UI tracks.**
   The source includes a Next.js dashboard implementation and a separate React SPA-style workspace, which required explicit documentation to reduce confusion.
4. **Documentation needed consolidation around installer, starter, manuals, and UX/UI guidance.**
   This update addresses that gap by expanding the platform overview, installation, quick-start, configuration, manuals, and admin-panel UI docs.

## Commands useful for reproducing the scan

```bash
rg --files -g 'README*' -g '*.md' -g '!node_modules' -g '!dist' -g '!build' -g '!coverage'
python - <<'PY'
import yaml
with open('docker compose.yml') as f:
    data=yaml.safe_load(f)
print('\\n'.join(data['services'].keys()))
PY
sed -n '1,260p' docker compose.yml
sed -n '1,240p' scripts/zttato-node.sh
sed -n '1,260p' configs/nginx.conf
pytest
```

## Documentation update result

The following doc areas were refreshed in this pass:
- repository README
- system overview
- project structure
- installation guide
- quick-start guide
- configuration reference
- user/admin/devops/godmode manuals
- admin-panel service doc
- new UX/UI guide for admin-panel

## Recommended next actions

- decide whether the Next.js or SPA admin-panel path is canonical
- expose additional internal services only after documenting auth and ownership
- continue keeping “baseline runtime” and “extended platform graph” clearly separated in docs and ops playbooks
- re-run `pytest` and service-specific frontend builds whenever UI/runtime changes accompany future documentation updates
