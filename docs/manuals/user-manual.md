# User Manual

## 1) Purpose

This manual is for business operators and day-to-day users of zTTato workflows. It focuses on how to use the currently exposed platform endpoints and what to expect from the broader stack.

## 2) What users interact with today

In the default local stack, the main user-facing entrypoint is the Nginx gateway at `http://localhost`. Through that gateway, users can reach:

- `POST /predict` — submit video engagement inputs and receive a virality score.
- `POST /crawl` — submit a product keyword to queue a crawl job.
- `GET /arbitrage` — retrieve the current highest-profit arbitrage records.
- `GET /` — basic gateway health response.

In expanded deployments, users may also interact with:
- the `admin-panel` Next.js frontend
- analytics dashboards
- click-tracking and campaign workflows
- auth-protected interfaces using the JWT service

## 3) Access expectations

### Local baseline access
- Gateway: `http://localhost`
- Predictor route: `http://localhost/predict`
- Crawler route: `http://localhost/crawl`
- Arbitrage route: `http://localhost/arbitrage`

### Expanded environment access
Actual URLs may differ in staging or production depending on Nginx, Cloudflare, or Kubernetes ingress configuration.

If access fails, contact an administrator with the exact URL, timestamp, and error message.

## 4) Standard user workflows

### A) Score a content candidate

Use `/predict` when you want a quick virality estimate for a piece of content.

Example request:

```bash
curl -X POST http://localhost/predict \
  -H 'content-type: application/json' \
  -d '{"views":1000,"likes":100,"comments":10,"shares":5}'
```

Good practice:
- use realistic engagement numbers
- compare results across multiple candidate assets
- treat the score as a ranking aid, not a guaranteed outcome

### B) Queue a crawl job

Use `/crawl` to request product discovery around a keyword.

```bash
curl -X POST http://localhost/crawl \
  -H 'content-type: application/json' \
  -d '{"keyword":"wireless earbuds"}'
```

Good practice:
- use concise product or niche keywords
- avoid sending the same request repeatedly if the queue is already backed up
- record which keyword set was submitted when comparing outcomes

### C) Review arbitrage output

Use `/arbitrage` to inspect the top arbitrage rows currently available in PostgreSQL.

```bash
curl http://localhost/arbitrage
```

Good practice:
- focus on relative profit and source combinations
- validate source freshness before acting on any opportunity
- coordinate with admins if data appears stale or unexpectedly empty

## 5) Data quality rules

- Use consistent naming for products and campaign inputs.
- Avoid duplicate submissions unless you are intentionally re-running a job.
- Include the full required JSON payload for API requests.
- Keep a record of the time and input used for important decisions.

## 6) Security and acceptable use

- Never share account credentials, JWTs, or secrets in tickets or chat.
- Do not upload unauthorized source data or media.
- Do not use break-glass or admin-only workflows without approval.
- Report suspicious access patterns immediately.

## 7) Common problems and self-service checks

### Gateway unreachable
- confirm `http://localhost/` responds
- ask an admin to run `docker compose ps`
- confirm the stack was started successfully

### `/predict` returns errors
- validate JSON formatting
- confirm all numeric fields are present
- retry once before escalating

### `/crawl` queues but results seem delayed
- the crawler uses background workers and Redis-backed queues
- ask an admin whether worker backlog is increasing
- avoid flooding the queue with duplicate keywords

### `/arbitrage` returns no useful data
- ask whether `arbitrage_events` has recent rows
- confirm database initialization completed
- ask whether upstream discovery/pipeline jobs have produced new data

## 8) Escalation template

When reporting an issue, include:
- date and time with timezone
- environment or URL used
- exact endpoint or page
- request payload shape if relevant
- expected behavior
- actual behavior
- any response code or error text
- whether the problem is constant or intermittent
