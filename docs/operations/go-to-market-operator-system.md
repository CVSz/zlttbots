# Go-To-Market Operator System

This runbook converts growth ideas into deterministic execution primitives that can be tracked and tested.

## Assets implemented

- `enterprise_maturity/go_to_market.py`
  - Daily phase planner (`generate_daily_plan`) for day-based execution windows.
  - Deterministic content generator (`generate_post`) using slot-based hook rotation (no randomness).
  - Pitch deck skeleton generator (`generate_pitch_deck_outline`) with typed traction metrics.
  - Date-stamped status helper (`generate_date_stamped_status`) for investor updates.
- `tests/test_go_to_market_system.py`
  - Phase objective validation.
  - Deterministic content behavior verification.
  - Pitch/status metric rendering checks.

## Daily execution model

### Morning (Product + Metrics)
1. Validate signup-to-deploy flow.
2. Fix at least one bug.
3. Improve one UX friction point.
4. Review users/deploys/failures.

### Midday (Distribution)
1. Publish three posts.
2. Send 20 targeted developer outreach messages.

### Evening (Retention + Proof)
1. Increase visibility of AI-assisted fix flow.
2. Reply to all inbound user messages.
3. Capture feedback from three users.

## KPI defaults

- Users/day: 50-100
- Deploys/day: 100+
- Shares/day: increasing trend required

## Usage example

```python
from enterprise_maturity.go_to_market import ContentInput, DeckMetrics, generate_daily_plan, generate_post

plan = generate_daily_plan(4)
post = generate_post(ContentInput(product_link="https://zlttbots.dev", social_proof_count=120), slot=1)
metrics = DeckMetrics(users=320, deploys=1180, daily_growth_percent=12.4)
```

This structure is production-safe for automation pipelines because inputs are validated and output selection is deterministic.
