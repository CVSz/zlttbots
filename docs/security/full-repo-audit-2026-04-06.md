# Full Repository Security & Reliability Audit

**Repository:** `zttato-platform`  
**Audit date (UTC):** 2026-04-06  
**Auditor:** Codex autonomous agent

## Scope

- Reviewed all tracked files (`git ls-files`): **659 files**.
- Performed focused static review of:
  - API gateway and Node services under `apps/*`
  - Security-sensitive service `services/jwt-auth`
  - CI/CD workflow and security scan scripts
  - Compose/runtime configuration and environment handling

## Methodology

1. Enumerated tracked repository files and service topology.
2. Ran pattern-based secret detection and dangerous API scans across tracked code.
3. Performed manual code review on authentication, authorization, crypto, and payment webhook paths.
4. Reviewed CI pipeline coverage and dependency scan implementation.

## Executive Summary

The repo has a strong baseline in several places (JWT validation in the gateway, schema validation with Zod, argon2id hashing in auth-service, SAST/DAST steps in CI). However, there are **critical/high-risk gaps** that should be prioritized:

- A tracked `.env` file contains deployable credentials/default secrets.
- Stripe webhook endpoint processes events without signature verification.
- `platform-core` has unreachable quota/tenant enforcement logic because of an early `return`.
- Internal services rely heavily on perimeter trust and can be bypassed if directly reachable.

## Findings

## 1) Critical — Sensitive `.env` file committed to repository

**Impact:** Credential leakage, accidental environment reuse, and insecure defaults being propagated into non-dev environments.

**Evidence:**
- `.env` contains `DB_PASSWORD=zttato` and other environment values.
- `.gitignore` excludes `.env`, but the file is already tracked, so ignore rules do not protect existing tracked secrets.

**Recommendation:**
- Remove `.env` from git history and current tracking (`git rm --cached .env`).
- Rotate any credentials that may have been exposed.
- Keep `.env.example` only, with non-secret placeholders.

## 2) High — Stripe webhook endpoint does not verify signature

**Impact:** Anyone who can access `/webhook` can forge `checkout.session.completed` events and upgrade plans without a real Stripe payment.

**Evidence:**
- `apps/billing-service/src/index.ts` trusts `req.body` directly and does not call Stripe signature verification (`stripe.webhooks.constructEvent(...)`).

**Recommendation:**
- Validate Stripe signatures with `Stripe-Signature` header and shared endpoint secret.
- Use raw body parser for webhook route and reject unverifiable requests.

## 3) High — Authorization/quota logic in `platform-core` is unreachable

**Impact:** Tenant limit checks and additional deployment controls are effectively disabled in `/deploy` due to control-flow bug.

**Evidence:**
- `apps/platform-core/src/index.ts` returns response after initial queueing path, then contains additional quota checks and deployment bookkeeping that can never execute.

**Recommendation:**
- Refactor `/deploy` into a single deterministic execution path with checks before side effects.
- Add unit/integration tests ensuring quota enforcement executes.

## 4) High — Defense-in-depth gap: multiple services miss local hardening middleware

**Impact:** If services are reachable directly (misconfigured network policy, sidecar bypass, exposed port), they lack independent protections such as request throttling and security headers.

**Evidence:**
- `apps/api-gateway` includes `helmet` and `express-rate-limit`, but peer services (e.g., `apps/auth-service`, `apps/billing-service`, `apps/log-service`, `apps/platform-core`, `apps/worker-ai`) do not apply equivalent middleware.

**Recommendation:**
- Apply minimal service-level controls (rate limiting, payload caps per route, optional internal auth token validation).
- Enforce Kubernetes/compose network policy so only gateway reaches internal apps.

## 5) Medium — Weak TLS verification option in database client config

**Impact:** Potential MITM risk when `DB_SSL_MODE=require` because cert chain verification is explicitly disabled.

**Evidence:**
- `apps/platform-core/src/index.ts` uses `ssl: { rejectUnauthorized: false }`.

**Recommendation:**
- Use managed CA bundle and `rejectUnauthorized: true` in production.
- Fail closed when secure TLS trust cannot be established.

## 6) Medium — Custom JWT implementation increases crypto maintenance risk

**Impact:** Bespoke token encoding/decoding is harder to validate and maintain compared with mature JWT libraries; subtle parsing/claim/alg handling mistakes can become auth bypasses over time.

**Evidence:**
- `services/jwt-auth/src/main.py` manually builds/parses token parts and HMAC signatures instead of using a standard JOSE/JWT library.

**Recommendation:**
- Replace custom encode/decode with vetted library (e.g., `pyjwt`/`python-jose`) and explicit algorithm allowlist.
- Add negative tests for malformed tokens and claim edge cases.

## 7) Medium — Node dependency scanning coverage is incomplete for repo layout

**Impact:** Vulnerabilities in `apps/*` Node packages may be missed by CI dependency scanning.

**Evidence:**
- `infrastructure/scripts/node-dependency-scan.sh` scans only `services/*/package.json`.
- Node-based apps exist under `apps/*` and are not covered by this script.

**Recommendation:**
- Extend dependency scan script to include `apps/*` and root workspace packages where applicable.
- Enforce lockfile presence per package before CI audit step.

## Positive controls observed

- `apps/auth-service` hashes passwords with **argon2id**.
- `apps/api-gateway` enforces JWT verification with issuer/audience checks and applies helmet + rate limiting.
- CI includes Bandit SAST, Trivy filesystem scanning, and a ZAP baseline DAST stage.

## Prioritized remediation order

1. Remove tracked secrets and rotate credentials.
2. Fix Stripe webhook signature validation.
3. Fix unreachable authorization/quota logic in `platform-core`.
4. Add service-level hardening middleware + network isolation controls.
5. Tighten TLS verification and standardize JWT library usage.
6. Broaden CI dependency scan scope.

## Commands executed

```bash
git ls-files | wc -l
rg --files -g 'AGENTS.md'
rg --files -g 'package.json' -g 'pyproject.toml' -g 'requirements*.txt' -g 'go.mod' -g 'Cargo.toml'
rg -n --no-heading -e 'AKIA[0-9A-Z]{16}' -e '-----BEGIN (RSA|EC|OPENSSH|DSA) PRIVATE KEY-----' -e '(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*["\x27][^"\x27]{8,}["\x27]' $(git ls-files)
rg -n --no-heading -e '\beval\(' -e 'exec\(' -e 'subprocess\.(Popen|run)\(.+shell\s*=\s*True' -e 'child_process\.exec\(' $(git ls-files)
rg -n --no-heading -e 'yaml\.load\(' -e 'pickle\.loads\(' -e 'md5\(' -e 'sha1\(' -e 'verify=False' -e 'jwt\.decode\([^\)]*verify\s*=\s*False' $(git ls-files '*.py' '*.ts' '*.js')
npm audit --workspaces --audit-level=high
```

