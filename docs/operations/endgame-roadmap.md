# zTTato Endgame Roadmap (Reality-Based Execution Order)

เอกสารนี้แปลง roadmap แบบ “endgame” ให้เป็นลำดับลงมือทำที่ผูกกับ repo ปัจจุบัน โดยเน้น production-first และเงินเข้าได้จริงก่อนฝันไกล.

## Stage 0 — Right now: stabilize the existing stack

**Goal:** ให้ stack ที่มีอยู่รันซ้ำได้, debug ได้, และไม่พังง่าย.

### Action checklist
- Validate both compose files in CI (`docker compose.yml` and `docker compose.enterprise.yml`).
- Ensure every HTTP-facing service exposes `/healthz` and Compose health checks.
- Standardize external API calls with timeout, retry, and backoff.
- Emit structured JSON logs so Loki/Promtail can ingest all services consistently.
- Add global exception handlers on services that are still returning raw tracebacks.

### Exit criteria
- Compose files parse cleanly and do not hide services under the wrong YAML section.
- Health checks can tell apart `ok` vs `degraded`.
- A failing upstream call returns a controlled 502/5xx instead of hanging forever.

## Stage 1 — Real data before real AI

**Goal:** replace mock/fake loops with a measurable data pipeline.

### First production tickets
1. Create Kafka topics: `raw_events`, `cleaned_events`, `training_data`.
2. Define JSON schema for each topic and reject invalid payloads.
3. Add deduplication keys for crawled items and click/conversion events.
4. Store labeled outcomes that tie content -> traffic -> conversion -> payout.
5. Build a daily data-quality report: freshness, null rate, duplicate rate, schema drift.

### Exit criteria
- Every model-training row is traceable back to a real campaign or content event.
- The team can answer: “which source created this revenue signal?”

## Stage 2 — Profit mode before scale mode

**Goal:** prove one funnel can generate revenue with controlled CAC before scaling automation.

### Required path
1. Pick one channel and one monetization path only.
2. Instrument the funnel end-to-end: impression -> click -> landing -> conversion -> payout.
3. Enforce budget caps per campaign and a global kill switch.
4. Track margin, refund rate, and payback window daily.
5. Pause any campaign that lacks attributable ROI.

### Recommended rule
> No scaling to 100 campaigns until 1 campaign shows repeatable positive unit economics.

## Stage 3 — Real AI only after data + ROI proof

**Goal:** upgrade from heuristics to models that improve an already-working funnel.

### Build order
1. Feature store for ranking/trend/payout features.
2. Offline training pipeline with versioned datasets.
3. Online inference service with rollbackable model versions.
4. Evaluation gates: baseline comparison, canary, rollback, audit trail.

### Exit criteria
- A model deployment is reversible and measurable.
- "AI improvement" means better revenue, margin, or conversion — not just a smarter demo.

## Stage 4 — Everything else is conditional

Long-horizon phases such as multi-region, self-improving agents, DAO/governance, decentralization, and autonomous-org ideas only make sense **after**:
- the stack is stable,
- data is trustworthy,
- one funnel makes money,
- cost controls are enforced,
- deployment and rollback are boring.

## What changed in this repository now

This repository update supports Stage 0 directly:
- `docker compose.enterprise.yml` now keeps enterprise services under `services:` instead of accidentally nesting them under `volumes:`.
- `product-discovery` now has `/healthz`, retry/timeout handling, structured JSON logging, and global exception handling.
- The service Dockerfile now installs pinned dependencies from `requirements.txt` for repeatable builds.
