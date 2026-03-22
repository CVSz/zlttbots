# Profit System Blueprint (Deployable)

This blueprint documents the production-safe implementation added for a measurable profit loop:

- tracking redirect service,
- Stripe webhook ingestion,
- ROI decision engine,
- autonomous scale/pause loop,
- daily cost guard,
- TikTok uploader tracking-link response.

## Required environment

```bash
export BASE_URL=https://api.zeaz.dev
export AFFILIATE_BASE_URL=https://your-aff-link.example/offer
export STRIPE_WEBHOOK_SECRET=whsec_xxx
export MAX_DAILY_COST=300
export ROI_THRESHOLD=1.2
export DATABASE_URL=postgresql://...
```

## Components

- `services/tracking/server.py`: `/t/{campaign_id}` click tracking and redirect.
- `services/payment/webhook.py`: `/webhook` Stripe event verification and order persistence.
- `services/analytics/roi.py`: deterministic ROI computation API.
- `services/core/profit_loop.py`: autonomous run-once decision engine (`scale` / `hold` / `pause`).
- `services/cost/guard.py`: daily spend guard with explicit reset behavior.
- `services/tiktok-uploader/src/api.ts`: upload helper now returns `tracking_link` bound to campaign.

## Notes

- All components validate required inputs.
- Webhook processing explicitly rejects missing `campaign_id`, `click_id`, or `event_id`.
- ROI and profit-loop decisions are deterministic for the same inputs.
- Governance, human-override, and business-infrastructure controls are documented in `docs/operations/profit-system-governance.md`.
