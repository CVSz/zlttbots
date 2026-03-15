# Service SLO Catalog

## SLO baseline

Each service must publish these indicators:

1. Availability (% successful requests per rolling 28 days)
2. Latency (p95)
3. Data freshness or queue completion latency

## Initial targets

| Service | Availability | p95 latency | Freshness/Completion |
|---|---:|---:|---:|
| Public APIs | 99.9% | <= 400 ms | <= 5 min |
| Internal APIs | 99.5% | <= 800 ms | <= 10 min |
| Workers | 99.0% | n/a | <= 15 min queue completion |

## Error budgets

- 99.9% SLO => 43m 49s monthly error budget.
- 99.5% SLO => 3h 39m monthly error budget.
- 99.0% SLO => 7h 18m monthly error budget.

## Review cadence

- Weekly reliability review on burn rate and top error contributors.
- Release gate blocks high-risk rollouts when budget burn exceeds threshold.
