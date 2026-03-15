# Project Structure

```text
zttato-platform/
├── docs/                    # Documentation, runbooks, manuals, architecture
├── services/                # Business services (Node.js/Python)
│   ├── admin-panel/
│   ├── analytics/
│   ├── arbitrage-engine/
│   ├── click-tracker/
│   ├── gpu-renderer/
│   ├── market-crawler/
│   ├── viral-predictor/
│   └── ...
├── infrastructure/          # k8s manifests, CI scripts, startup tooling, postgres assets
├── scripts/                 # Operations helpers (deploy, repair, monitor, doctor)
├── contracts/               # Service API/data contracts
├── configs/                 # Shared env and gateway configuration
├── tests/                   # Python test suite
├── docker-compose.yml       # Default orchestration baseline
└── README.md
```

## Directory intent

- **`docs/`**: authoritative operational and developer documentation.
- **`services/`**: independently deployable components with per-service dependencies.
- **`infrastructure/`**: platform orchestration and production-oriented artifacts.
- **`scripts/`**: repeatable command wrappers for diagnostics, deploy, and recovery.
- **`tests/`**: baseline validation for core Python modules.
