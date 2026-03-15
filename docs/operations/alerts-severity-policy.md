# Alert Severity and Routing Policy

## Severity model

- **SEV-1:** Major user impact, critical revenue/system path broken.
- **SEV-2:** High impact degradation with workaround.
- **SEV-3:** Limited impact, non-critical function degraded.
- **SEV-4:** Informational or low urgency operational issue.

## Routing rules

1. All alerts require `owner`, `service`, `severity`, and `runbook` labels.
2. SEV-1/SEV-2 route to primary + secondary on-call and incident channel.
3. SEV-3 routes to service queue with same-day triage.
4. SEV-4 routes to backlog with weekly review.

## SLA

- SEV-1 acknowledge in 5 min.
- SEV-2 acknowledge in 15 min.
- SEV-3 acknowledge in 4 business hours.
- SEV-4 acknowledge in 2 business days.
