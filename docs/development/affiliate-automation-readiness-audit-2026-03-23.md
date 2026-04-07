# Affiliate Automation Readiness Audit (2026-03-23)

## Request Context

This audit was executed to re-check the repository in detail against these required outcomes:

1. TikTok + Shopee + Lazada affiliate API flow.
2. Pull high-commission products.
3. Auto-create and auto-post 30 videos/day.
4. Verify reporting for posted products.

---

## Method

The review used source-level inspection of crawler, arbitrage, video, uploader, orchestrator, analytics, and infra wiring, plus test baseline verification.

Validation command run:

- `pytest -q` → `63 passed, 5 skipped`.

---

## Detailed Findings by Requirement

## 1) TikTok + Shopee + Lazada affiliate API integration

### Current state: **Partially implemented / not production-complete**

- Shopee and Lazada product crawling paths exist in `market-crawler` and produce normalized product records with source tagging. (`crawl_shopee`, `crawl_lazada`, worker ingestion loop). 
- TikTok product mining exists separately in `tiktok-shop-miner`.
- Shopee crawler service generates a simple affiliate link format (`aff_id=ZLTTBOTS`) when storing products.
- Execution publishing is platform-agnostic (`PLATFORM_API_BASE/content/publish`) and does not implement concrete official TikTok/Shopee/Lazada partner API contracts in this repo.

### Gaps blocking “full efficiency” claim

- No unified cross-network affiliate connector module that authenticates and normalizes all three partner APIs in one deterministic pipeline.
- Shopee/Lazada ingestion logic relies on public endpoints/HTML selectors without explicit API auth and without resilient schema-contract handling.
- No repository-level signed, vendor-specific API client for Shopee/Lazada commissions/orders callbacks.

---

## 2) High-commission product selection

### Current state: **Basic heuristic only / not true high-commission optimization**

- Arbitrage module has hardcoded commission rates (`shopee=0.07`, `lazada=0.08`, `amazon=0.05`) and computes simple profit estimate from source differences.
- Product ingestion stores price/sales/rating, but no authenticated commission feed, no dynamic payout tiers, no campaign-level EPC/CVR-driven ranking.

### Gaps

- No direct ingestion of real affiliate commission metadata per SKU.
- No scoring model that prioritizes “highest commission with conversion likelihood” end-to-end.
- No fallback/quality gates for stale commission data.

---

## 3) Automatic video generation + posting 30 videos/day

### Current state: **Automation loop exists but target control missing**

- Video generation worker continuously polls pending jobs and marks done.
- TikTok uploader worker continuously polls pending videos and marks posted.
- Workers process one pending item per loop (`limit 1`) with fixed sleeps (10s/15s).

### Gaps

- No explicit scheduler policy guaranteeing **exactly 30 videos/day** per tenant/account/campaign.
- No quota ledger or daily counter enforcement tied to date boundaries.
- Account selection uses random ordering in uploader worker, reducing determinism and making throughput guarantees unreliable.
- No backpressure/SLA logic proving daily completion under failure conditions.

---

## 4) Reporting for posted products

### Current state: **Partial analytics present / posted-product report not fully closed-loop**

- Analytics service exposes summary/revenue/conversion/campaign/product endpoints.
- Affiliate webhook writes conversion metrics and forwards to feature/reward services.
- Uploader marks video status as `posted`.

### Gaps

- No explicit report endpoint that joins posted video IDs ↔ source product IDs ↔ affiliate revenue outcome as one auditable posted-product report.
- No documented daily report artifact for “what was posted today, where, and with what commission/revenue result.”

---

## Operational Risk Assessment

- **Delivery risk:** Medium-high for guaranteed 30/day output due to missing quota scheduler and deterministic dispatch.
- **Revenue risk:** High for commission optimization accuracy because commission values are static heuristics.
- **Compliance/maintainability risk:** Medium due to direct scraping-style paths and absence of explicit partner API contract wrappers.

---

## Conclusion

As of **March 23, 2026**, the repository has substantial building blocks for affiliate automation, but it does **not yet satisfy the requested full-performance state** for:

- unified TikTok+Shopee+Lazada affiliate API execution,
- high-commission product optimization from authoritative payout data,
- deterministic 30-videos/day auto-post guarantee,
- complete posted-product outcome reporting.

---

## Priority Remediation Plan (Recommended)

1. Build a unified affiliate connector layer (`tiktok/shopee/lazada`) with typed contracts and auth-backed commission/order retrieval.
2. Replace static commission constants with dynamic per-product payout ingestion + freshness timestamps.
3. Add deterministic daily publishing controller (target=30/day, per-tenant counters, retry budget, dead-letter queue).
4. Add posted-product reporting API/table that joins: product, video, publish result, clicks, conversions, revenue, commission rate.
5. Add integration tests for the above flow plus daily target assertions.

