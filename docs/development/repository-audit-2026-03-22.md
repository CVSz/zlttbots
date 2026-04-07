# Repository Audit Report (2026-03-22)

This report summarizes a focused review of the codebase to identify actionable work in four areas requested by the team:

1. text and typo fixes,
2. bug fixes,
3. comment/documentation mismatch corrections,
4. test quality improvements.

Scope reviewed:
- root documentation and operational docs,
- Python test suite,
- selected service entrypoints and scripts referenced by docs.

---

## Executive Summary

- Overall repository health is good: `pytest -q` passes (`47 passed, 5 skipped`).
- One concrete bug-quality issue was confirmed and fixed in this change set: deprecated TestClient usage that produced a warning.
- Documentation quality is generally strong, but there are a few consistency opportunities that should be handled as backlog tasks.

---

## Findings and Proposed Work

## A) Text / Typo / Wording Fixes

### A1. Clarify Python entrypoint wording in configuration docs
**Status:** Fixed in this PR.

**Problem**
`docs/configuration.md` implied every Python service uses `src/main.py`, which is not guaranteed across all services.

**Change made**
Wording now states that services use an entrypoint module, commonly `src/main.py`.

**Why it matters**
Reduces ambiguity for new contributors and avoids incorrect assumptions during debugging.

---

## B) Bug Fix Tasks

### B1. Remove deprecated FastAPI TestClient request pattern
**Status:** Fixed in this PR.

**Problem**
`tests/test_profit_mode_pipeline.py` used `client.post(..., data=body, ...)` with raw bytes, which triggers an `httpx` deprecation warning.

**Change made**
Switched to `content=body` for raw request payloads.

**Why it matters**
- Eliminates deprecation warning noise.
- Future-proofs tests against stricter `httpx` behavior.
- Keeps CI outputs cleaner and easier to triage.

---

## C) Comment / Documentation Mismatch and Consistency Tasks

### C1. Standardize command style across docs
**Priority:** Medium.

**Observed pattern**
Some docs use `./script.sh`, others use `bash script.sh`. Both are valid, but mixed style adds friction for copy-paste automation and onboarding.

**Proposed task**
- Define a repository-wide convention (recommended: `bash <script>` for clarity and no execute-bit dependency).
- Update `README.md`, `docs/installation.md`, `docs/quick-start.md`, and operations docs to match.

### C2. Cross-reference map for startup paths
**Priority:** Medium.

**Observed pattern**
Multiple startup flows exist (`start.sh`, `start-zlttbots.sh`, `scripts/zlttbots-manager.sh`). Docs mention them, but there is no single comparison table showing behavior differences.

**Proposed task**
Add a matrix documenting:
- what each script installs/starts,
- side effects (dependency installation, venv creation, service scope),
- suitable environments (local dev, CI smoke, enterprise rollout).

### C3. Validate all documentation command snippets in CI
**Priority:** High.

**Observed risk**
Command snippets may drift over time because they are not currently validated as executable examples.

**Proposed task**
Introduce a doc-check job that validates shell blocks (or tagged blocks) with a lightweight script (e.g., parsing markdown and dry-running allowed commands).

---

## D) Testing Improvements (Detailed Backlog)

### D1. Add warning-free test gate
**Priority:** High.

**Task**
Add a CI target using `pytest -W error::DeprecationWarning` (or scoped warning filters).

**Benefit**
Deprecations are caught proactively instead of accumulating.

### D2. Expand integration tests for script-based lifecycle
**Priority:** High.

**Task**
Add non-destructive integration tests for:
- `scripts/zlttbots-manager.sh` key subcommands,
- `start.sh` sanity behavior,
- selected infrastructure validators.

**Benefit**
Protects operational workflows that are critical in production-like environments.

### D3. Add documentation-driven smoke tests
**Priority:** Medium.

**Task**
Create tests that assert key docs reference real files and executable scripts (e.g., documented paths exist).

**Benefit**
Prevents doc rot and broken onboarding paths.

### D4. Track skipped tests explicitly
**Priority:** Medium.

**Task**
For each skipped test, document skip reason and required environment in a small test matrix (`docs/development/testing.md` extension or generated report).

**Benefit**
Improves transparency and prioritization for broader test coverage.

---

## Recommended Implementation Sequence

1. Enforce warning-free test execution in CI.
2. Add script lifecycle integration smoke tests.
3. Standardize command style in docs.
4. Add docs path/snippet validation automation.
5. Add startup-path comparison matrix.

This order is chosen to maximize reliability and reduce regression risk first.
