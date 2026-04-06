# 24-Hour Go-Live Checklist

## Hour 0–4 (Setup)

- [ ] Configure production `.env` (JWT secret, CORS allow-list, database URL).
- [ ] Provision PostgreSQL (Supabase or managed Postgres).
- [ ] Run `docker compose up -d` and verify all core services are healthy.
- [ ] Verify TLS and DNS are configured for the primary domain.

## Hour 4–8 (Core Flow Validation)

- [ ] Signup/login flow passes end-to-end checks.
- [ ] Deploy endpoint returns `202 QUEUED` with deploy ID.
- [ ] Deployment events are persisted in `deployments` table.
- [ ] Structured logs stream correctly from gateway and platform-core.

## Hour 8–12 (Domain + Edge)

- [ ] Configure Cloudflare DNS records.
- [ ] Validate API and frontend origins from a public network.
- [ ] Confirm security headers, CORS policy, and rate limiting.

## Hour 12–18 (Polish)

- [ ] Validate landing page conversion path (hero → CTA → deploy flow).
- [ ] Validate deploy demo messaging for the AI-fix hook.
- [ ] Fix UI issues affecting signup/deploy conversion.

## Hour 18–24 (Launch)

- [ ] Publish launch post on X/Twitter, Reddit, and TikTok.
- [ ] Monitor error rate and request latency.
- [ ] Capture first-user feedback and prioritize top 3 blockers.
