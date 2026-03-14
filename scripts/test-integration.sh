#!/usr/bin/env bash
set -euo pipefail

COMPOSE_CMD=(docker compose)
BASE_URL="${BASE_URL:-http://127.0.0.1:80}"
SERVICES=(postgres redis viral-predictor market-crawler arbitrage-engine gpu-renderer nginx)

log() {
  printf '[integration] %s\n' "$*"
}

assert_running() {
  local svc="$1"
  local state
  state="$(${COMPOSE_CMD[@]} ps --format json "$svc" | python -c 'import json,sys; data=json.load(sys.stdin); print(data[0]["State"] if data else "missing")')"

  if [[ "$state" != "running" ]]; then
    log "service '$svc' is not running (state=$state)"
    return 1
  fi

  log "service '$svc' is running"
}

assert_http_2xx() {
  local method="$1"
  local url="$2"
  local body="${3:-}"
  local code

  if [[ -n "$body" ]]; then
    code="$(curl -sS -o /dev/null -w '%{http_code}' -X "$method" -H 'content-type: application/json' -d "$body" "$url")"
  else
    code="$(curl -sS -o /dev/null -w '%{http_code}' -X "$method" "$url")"
  fi

  if [[ "$code" -lt 200 || "$code" -ge 300 ]]; then
    log "request failed: $method $url (http=$code)"
    return 1
  fi

  log "request ok: $method $url (http=$code)"
}

log "starting compose stack"
${COMPOSE_CMD[@]} up -d

log "checking service process state"
for svc in "${SERVICES[@]}"; do
  assert_running "$svc"
done

log "running HTTP smoke tests via nginx"
assert_http_2xx GET "$BASE_URL/"
assert_http_2xx POST "$BASE_URL/predict" '{"views":1000,"likes":100,"comments":10,"shares":5}'
assert_http_2xx POST "$BASE_URL/crawl" '{"keyword":"wireless earbud"}'
assert_http_2xx GET "$BASE_URL/arbitrage"

log "integration smoke test passed"
