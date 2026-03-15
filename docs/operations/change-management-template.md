# High-Risk Change Management Template

Use this template for production changes with elevated operational, security, or data risk.

## 1) Change overview

- **Change title:**
- **Tracking ID:**
- **Owner:**
- **Date/time window:**
- **Affected services:**
- **Environment:**
- **Deployment strategy:** Blue/Green | Canary | Rolling | Other

## 2) Business and technical justification

- **Why this change is required now:**
- **Expected user/business impact:**
- **Alternatives considered:**

## 3) Risk assessment

- **Risk level:** Low | Medium | High | Critical
- **Primary risks:**
- **Dependencies and prerequisites:**
- **Security/compliance impact:**
- **Data/PII impact:**

## 4) Pre-deploy checklist

- [ ] CI required gates passed (unit, integration, security, image scan)
- [ ] Release artifact and version tagged
- [ ] Backups/snapshots verified
- [ ] Feature flag plan defined (if applicable)
- [ ] On-call and stakeholders notified
- [ ] Rollback command tested in staging
- [ ] Runbook links attached

## 5) Rollout plan

1. **Step 1:**
2. **Step 2:**
3. **Step 3:**
4. **Validation checkpoints:**

## 6) Observability and success criteria

- **SLOs monitored during rollout:**
- **Dashboards/alerts used:**
- **Success thresholds:**
- **Abort thresholds:**

## 7) Rollback plan

- **Rollback trigger conditions:**
- **Rollback procedure:**
- **Rollback owner:**
- **Data recovery steps (if needed):**

## 8) Communications plan

- **Pre-change announcement:**
- **Live status channel:**
- **Post-change report recipients:**

## 9) Approvals

- **Engineering owner approval:**
- **Security approval:**
- **SRE/on-call approval:**
- **Product/business approval (if required):**

## 10) Post-implementation review

- **Outcome:** Success | Partial | Failed
- **Incidents/issues observed:**
- **Follow-up actions and owners:**
- **Lessons learned:**
