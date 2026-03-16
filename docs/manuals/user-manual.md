# User Manual

## 1. Purpose

This manual is for business operators using zTTato workflows through dashboard and API-facing features.

## 2. What a user can do

Typical user-level activities:

- Review discovered products and campaign candidates.
- Trigger prediction or analysis workflows via supported APIs/tools.
- Monitor campaign results and move budget toward better performers.
- Escalate anomalies to admins with reproducible context.

## 3. Access

Primary local endpoints:

- Dashboard (frontend workflow): `http://localhost:5173`
- API gateway: `http://localhost`
  - `GET/POST /predict`
  - `GET/POST /crawl`
  - `GET/POST /arbitrage`

If access fails, contact an administrator to verify environment status and role permissions.

## 4. Standard operating workflow

### A) Product discovery

1. Run or wait for crawler workflows.
2. Review candidate freshness and source quality.
3. Mark shortlist items for prediction and campaign planning.

### B) Prediction and ranking

1. Submit or trigger prediction calls.
2. Compare *relative* score differences rather than absolute certainty.
3. Promote high-score/high-feasibility candidates.

### C) Campaign optimization

1. Monitor click/conversion trend movement.
2. Pause weak assets early to reduce waste.
3. Reallocate resources to high-conversion opportunities.

## 5. Input quality rules

- Use consistent product identifiers (avoid duplicated naming variants).
- Submit complete payloads; avoid sparse fields where optional context improves scoring.
- Use realistic campaign assumptions when requesting prioritization.
- Avoid repeated duplicate submissions when queue lag already exists.

## 6. Safety and security rules

- Never share credentials in chat, tickets, or screenshots.
- Never paste secrets into dashboard free-text fields.
- Do not upload or submit data without source authorization.
- Report suspicious account behavior immediately.

## 7. Common issues and self-checks

### Dashboard unavailable

- Confirm URL is correct (`http://localhost:5173`).
- Check with admin whether frontend runtime is active.
- Check if core backend stack is healthy.

### API returns 5xx

- Retry once after a short delay.
- Capture timestamp, endpoint, and payload shape.
- Escalate to admin with exact response code/body snippet.

### Data seems stale

- Verify whether worker queues are backlogged.
- Ask admin for worker/service health status.
- Recheck after queue backlog clears.

## 8. Escalation template (recommended)

When filing an issue to admins, include:

- Time (with timezone)
- Endpoint/page impacted
- Steps to reproduce
- Expected vs actual behavior
- Error message/code
- Whether issue is persistent or intermittent
