# Safe go-live and edge blueprint

This project now includes a compliant edge blueprint for `*.zeaz.dev` that focuses on:

- first-party routing for approved platform services
- Zero Trust controls for human admin surfaces
- rate limiting and WAF protection for public APIs
- affiliate tracking and analytics that stay inside approved application boundaries

## Supported subdomains

| Hostname | Service | Notes |
| --- | --- | --- |
| `api.zeaz.dev` | Kong / API edge | Public API entry point with rate limiting |
| `admin.zeaz.dev` | Admin panel | Protect with Cloudflare Access |
| `auth.zeaz.dev` | JWT auth service | Keep behind Access or allowlisted clients |
| `ai.zeaz.dev` | AI video generator | Internal or approved operator workflows only |
| `crawl.zeaz.dev` | Market crawler | Approved discovery jobs only |
| `predict.zeaz.dev` | Viral predictor | API scoring endpoint |
| `grafana.zeaz.dev` | Monitoring UI | Internal-only |
| `kafka.zeaz.dev` | Kafka UI | Internal-only |

## Cloudflare Tunnel

Use `infrastructure/cloudflare/tunnel-config.example.yml` as the starting point for a tunnel configuration. Keep credentials out of git and mount them at runtime.

Recommended flow:

1. Create the tunnel.
2. Route each DNS hostname to the tunnel.
3. Run `cloudflared` with the checked-in example config adapted to your environment.

## Zero Trust and WAF

Recommended controls:

- `admin.zeaz.dev`: require SSO or OTP via Cloudflare Access.
- `grafana.zeaz.dev` and `kafka.zeaz.dev`: internal-only access policy.
- `api.zeaz.dev`: protect with WAF + rate limiting and application auth.
- service tokens for machine-to-machine access where appropriate.

## Go-live checklist

### Infrastructure

- Kubernetes or Docker environment healthy.
- Postgres backups enabled and tested.
- Redis and object storage sized for expected load.
- Monitoring stack reachable.

### Security

- JWT signing keys rotated and stored in a secret manager.
- Kong or ingress rate limits enabled.
- Cloudflare Access policies active on operator surfaces.
- WAF rules applied and reviewed.

### Application readiness

- Tracking redirects restricted to approved hosts.
- Manual approval step present before outbound publishing.
- Analytics summary endpoints returning data.
- Dashboard reflects current environment and partner metrics.

### Performance

- Load test completed for public API routes.
- HPA or equivalent worker scaling verified.
- Alert thresholds defined for error rate and queue backlog.

## Safety note

This repository intentionally supports approved affiliate tracking, analytics, content review, and operator workflows. Do not use it to automate account creation, evade platform safeguards, or perform spam posting.
