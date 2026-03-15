# User Manual

## 1. Purpose

This manual is for operators and business users who need to use zTTato Platform features without changing infrastructure or source code.

zTTato Platform is an automation and growth stack for social commerce and affiliate operations with API-driven workflows and a web dashboard.

---

## 2. Access Paths

### Dashboard

- Open the admin panel at `http://localhost:5173` in local environments.
- Use credentials provided by your organization.
- The dashboard includes campaign, products, and performance-oriented views.

### API Gateway

- Open API routes through the reverse proxy (default `http://localhost`).
- Key public paths:
  - `/predict`
  - `/crawl`
  - `/arbitrage`

---

## 3. Core User Workflows

### 3.1 Product Discovery Workflow

1. Trigger or request crawler activity (via admin workflows or platform automation).
2. Wait for crawler workers to collect marketplace data.
3. Review discovered products and profitability hints in product-facing dashboards.
4. Promote selected products to campaign pipelines.

### 3.2 Prediction Workflow

1. Submit product/content payloads to prediction endpoints.
2. Collect score outputs and ranking indicators.
3. Use scores to prioritize media generation and campaign budgets.

### 3.3 Campaign Optimization Workflow

1. Monitor click and conversion analytics.
2. Compare predicted performance with observed outcomes.
3. Pause low-performing campaigns.
4. Reallocate budget to higher-conversion products.

---

## 4. Dashboard Areas (High-Level)

Depending on your role and enabled modules, the platform frontend contains views such as:

- Overview dashboards
- Campaigns pages
- Products pages
- User/admin control panel pages
- Rent/admin operational views

If a page is missing, request role access from an administrator.

---

## 5. Data Interpretation Guidance

- **Conversion metrics**: prioritize stable trend lines over single spikes.
- **Prediction metrics**: treat model outputs as ranking signals, not guarantees.
- **Arbitrage outputs**: validate availability and logistics before execution.
- **Crawler freshness**: use recent crawl timestamps when selecting products.

---

## 6. User Safety and Account Hygiene

- Do not share dashboard credentials.
- Do not upload sensitive secrets into campaign notes or free-text fields.
- Avoid repeatedly submitting duplicate jobs; use existing queue status first.
- Report suspicious account behavior to administrators immediately.

---

## 7. Common User Issues

### Dashboard not loading

- Confirm containers are running.
- Confirm the frontend port (`5173`) is reachable.
- Ask admin to verify reverse proxy and service health.

### API returns 5xx

- Retry once after 30–60 seconds.
- If persistent, provide timestamp + endpoint + payload shape to support/admin.

### Missing recent analytics

- Data pipelines may be delayed.
- Ask admin to check worker and database health.

---

## 8. Expected Service Availability

A healthy platform should have these components running:

- PostgreSQL
- Redis
- Predictor service
- Crawler service
- Arbitrage service
- Renderer service
- Worker set (crawler, arbitrage, renderer)
- Nginx gateway

---

## 9. Escalation

Escalate issues to admins/devops with:

- Action attempted
- Exact time (UTC preferred)
- Endpoint/page used
- Error message and screenshot (if available)

This allows faster triage and recovery.
