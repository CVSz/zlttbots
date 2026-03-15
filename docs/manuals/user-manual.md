# User Manual

## 1. Purpose

This manual is for business operators using zTTato workflows through the dashboard and API-facing features.

## 2. Access

- Dashboard (local): `http://localhost:5173`
- API gateway (local): `http://localhost`
  - `/predict`
  - `/crawl`
  - `/arbitrage`

If access fails, contact an administrator for role or environment validation.

## 3. Typical workflows

### Product discovery

1. Trigger or wait for crawler pipelines.
2. Review discovered products and freshness metadata.
3. Move promising candidates into campaign planning.

### Prediction and ranking

1. Submit payloads for prediction.
2. Compare relative scores rather than treating a single score as certainty.
3. Prioritize assets with strong score + market viability.

### Campaign optimization

1. Monitor click and conversion trends.
2. Pause low-performing campaigns.
3. Reallocate budget to stronger products/content.

## 4. User safety rules

- Keep credentials private.
- Do not paste secrets into free-text dashboard fields.
- Avoid duplicate submissions when jobs are already queued.
- Report suspicious behavior immediately.

## 5. Common issues

### Dashboard unavailable

- Check with admin that core services are running.
- Validate `http://localhost:5173` connectivity.

### API 5xx responses

- Retry once after a short delay.
- Provide timestamp + endpoint + payload shape to support/admin.

### Missing recent analytics

- Data pipelines may be delayed.
- Ask admins to check worker health and queue lag.
