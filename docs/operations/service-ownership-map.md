# Service Ownership Map

| Service | Primary Owner | Secondary Owner | On-Call Channel |
|---|---|---|---|
| analytics | data-platform | sre-platform | #oncall-analytics |
| click-tracker | growth-platform | sre-platform | #oncall-growth |
| tiktok-uploader | creator-automation | sre-platform | #oncall-creator |
| ai-video-generator | ai-platform | sre-platform | #oncall-ai |
| shopee-crawler | commerce-ingestion | data-platform | #oncall-commerce |
| account-farm | automation-ops | security | #oncall-automation |
| admin-panel | product-admin | platform-web | #oncall-admin-ui |
| arbitrage-engine | arbitrage-team | sre-platform | #oncall-arbitrage |
| gpu-renderer | media-infra | sre-platform | #oncall-rendering |
| viral-predictor | ml-ranking | data-platform | #oncall-ml |
| market-crawler | commerce-ingestion | data-platform | #oncall-commerce |

## Escalation

- **SEV-1:** Primary owner + SRE incident commander in 5 minutes.
- **SEV-2:** Primary owner acknowledges in 15 minutes.
- **SEV-3/4:** Handled in business hours based on policy.
