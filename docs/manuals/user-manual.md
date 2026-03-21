# User Manual

This manual is the full-detail user guide for the currently accessible zTTato platform flows.

## 1) Who this manual is for

Use this manual if you are:
- an operator using the public/local gateway routes
- a product or campaign user reviewing scores or arbitrage output
- an internal teammate using the admin workspace after it has been started by your environment owner

## 2) What users can access today

### Baseline gateway routes
When the baseline stack is running, users interact with:

- `GET /` — gateway health confirmation
- `POST /predict` — virality scoring request
- `POST /crawl` — product crawl request
- `GET /arbitrage` — arbitrage listing

### Optional UI surface
In environments that also run the admin panel, users may see a browser UI for:

- overview metrics
- role-based navigation
- admin/user workspace views
- billing and rent-operation mock flows
- go-live and routing visibility in the Next.js dashboard path

## 3) Access expectations

### Local baseline access
- `http://localhost/`
- `http://localhost/predict`
- `http://localhost/crawl`
- `http://localhost/arbitrage`

### Extended environment access
Production/staging URLs can differ depending on nginx, PM2, Kubernetes ingress, or Cloudflare edge setup.

If you cannot access an expected route, capture:
- the exact URL
- the date/time with timezone
- the action attempted
- the returned message or status code

## 4) Core user workflows

### A. Score a content candidate
Use `/predict` to estimate a virality score.

```bash
curl -X POST http://localhost/predict \
  -H 'content-type: application/json' \
  -d '{"views":1000,"likes":100,"comments":10,"shares":5}'
```

Best practices:
- use realistic engagement values
- compare multiple candidates instead of trusting one result in isolation
- treat the output as decision support, not a guarantee

### B. Queue a discovery request
Use `/crawl` to request crawl work.

```bash
curl -X POST http://localhost/crawl \
  -H 'content-type: application/json' \
  -d '{"keyword":"wireless earbuds"}'
```

Best practices:
- use focused keywords
- avoid repeatedly submitting the same request without checking backlog
- log which keywords were sent and when

### C. Review arbitrage output
Use `/arbitrage` to inspect top arbitrage events stored in PostgreSQL.

```bash
curl http://localhost/arbitrage
```

Best practices:
- compare relative profit and source combinations
- confirm data freshness before acting operationally
- escalate stale results to admins

## 5) Using the admin workspace when available

If your environment includes the admin panel:
- sign in with the credentials supplied by your admin
- use the role-appropriate area only
- avoid changing admin-only settings unless authorized
- log out when finished on shared machines

Typical workspace areas may include:
- overview dashboard
- user dashboard
- admin dashboard
- access-control functions
- rent/billing workflow panels

## 6) Data quality guidance

- Use consistent product and campaign naming.
- Do not flood queues with duplicate requests.
- Keep request payloads complete and valid JSON.
- Record timestamps for important operational actions.
- Confirm whether returned data is sample/mock or production-backed in your environment.

## 7) Security and acceptable use

- Never share credentials, API keys, JWTs, or webhook secrets.
- Never use admin or break-glass workflows without approval.
- Do not upload unauthorized data or media.
- Report suspicious activity immediately.
- Treat locally documented demo credentials as development-only.

## 8) Common user problems

### Gateway unreachable
- verify `http://localhost/` or your assigned environment URL
- ask an admin to confirm container/process status
- include screenshot or raw response text in your report

### `/predict` errors
- verify numeric fields are present
- confirm JSON format is valid
- retry once, then escalate with payload and time

### `/crawl` accepted but nothing happens
- crawler processing is asynchronous
- the system may be healthy but backlogged
- ask admins to inspect worker and Redis queue state

### `/arbitrage` is empty or stale
- database may have no recent rows
- ingestion or upstream discovery may be delayed
- ask admins for freshness confirmation

### Admin panel sign-in fails
- confirm you are using the correct environment URL
- verify your assigned credentials
- ask whether the PM2/Node path is running in that environment

## 9) Escalation template

When reporting issues, include:
- date and time with timezone
- environment or URL
- endpoint or page name
- request payload shape if relevant
- expected behavior
- actual behavior
- any response code/error text
- whether it is constant or intermittent
