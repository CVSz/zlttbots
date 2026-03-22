# Profit System Governance and Real-World Controls

This document captures non-negotiable controls required to run the profit system safely in real business conditions.

## 1) Business infrastructure baseline

- Legal entity and banking setup must be verified before scaling spend.
- Tax/VAT obligations must be mapped per operating region.
- Payment settlement and payout reconciliation must be auditable.

## 2) Unit economics contract

The platform must publish and track at minimum:

- `CPA` (cost per acquisition),
- `LTV` (lifetime value),
- `ROAS` (return on ad spend),
- `profit` (`revenue - cost`).

Automation safety rule:

- if `profit < 0`, trigger stop-loss action immediately.

## 3) Risk and cost controls

Mandatory runtime controls:

- per-campaign budget cap,
- global daily kill switch,
- ROI threshold auto-stop,
- cost-spike anomaly detection.

## 4) Human override policy

Required operational controls:

- manual kill switch procedure,
- escalation policy for payment/tracking outages,
- auditable override events tied to operator identity.

## 5) Scale reliability controls

Before moving from 100 to 1,000+ campaigns:

- queue backpressure policy,
- circuit breaker coverage for external API calls,
- eventual consistency strategy for delayed conversion data.
