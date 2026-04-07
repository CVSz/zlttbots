# Gemini.md (Reviewed and Fixed)

This document was deep-reviewed and rewritten because the previous content mixed unrelated chat transcripts, unsafe commands, speculative patches, and partially generated code that was not safe to run in production.

## What was wrong in the previous version

- Included destructive cleanup commands without safety gates (`docker volume prune -f`, `git clean -fdx`, direct DB data deletion).
- Used host-wide prune behavior that can impact unrelated workloads on shared hosts.
- Contained speculative “scan/fix patch” output not validated against the repository state.
- Mixed multiple languages and long transcript fragments that reduced maintainability.
- Included incomplete code blocks and architecture claims without executable integration context.

## Fixed policy for cleanup and maintenance

1. **Safe by default**: no destructive operation runs without explicit confirmation.
2. **Scoped operations only**: target resources by Compose project name/labels.
3. **No direct DB file deletion while services are running**.
4. **Deterministic logging**: JSON log lines with explicit status.
5. **Production guardrails**: refuse destructive actions in `prod` unless a force flag is set.

## Production-safe `meta-clean` script

Path recommendation: `scripts/meta-clean.sh`

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_NAME="${PROJECT_NAME:-zlttbots}"
ENVIRONMENT="${ENVIRONMENT:-dev}"   # dev|staging|prod
CONFIRM="${CONFIRM:-false}"         # must be true to execute
FORCE_PROD="${FORCE_PROD:-false}"   # must be true when ENVIRONMENT=prod
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
TIMEOUT_SEC="${TIMEOUT_SEC:-20}"

log() {
  local level="$1" msg="$2"
  printf '{"ts":"%s","level":"%s","project":"%s","env":"%s","msg":"%s"}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$level" "$PROJECT_NAME" "$ENVIRONMENT" "$msg"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { log "ERROR" "missing command: $1"; exit 1; }
}

deny_if_unsafe() {
  [[ "$CONFIRM" == "true" ]] || { log "ERROR" "set CONFIRM=true to continue"; exit 1; }
  if [[ "$ENVIRONMENT" == "prod" && "$FORCE_PROD" != "true" ]]; then
    log "ERROR" "prod cleanup requires FORCE_PROD=true"
    exit 1
  fi
}

compose_down_scoped() {
  log "INFO" "stopping compose stack (scoped)"
  docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" down --remove-orphans --timeout "$TIMEOUT_SEC"
}

prune_scoped_images() {
  log "INFO" "pruning dangling images only"
  docker image prune -f
}

clean_build_cache() {
  log "INFO" "pruning build cache"
  docker builder prune -f
}

flush_redis_scoped() {
  local redis_container="${PROJECT_NAME}-redis"
  if docker ps --format '{{.Names}}' | grep -qx "$redis_container"; then
    log "INFO" "flushing redis in container: $redis_container"
    docker exec "$redis_container" redis-cli FLUSHDB
  else
    log "WARN" "redis container not found, skipping"
  fi
}

main() {
  require_cmd docker
  deny_if_unsafe

  compose_down_scoped
  prune_scoped_images
  clean_build_cache
  flush_redis_scoped

  log "INFO" "meta-clean completed"
}

main "$@"
```

## Usage examples

```bash
# Safe dev cleanup
CONFIRM=true PROJECT_NAME=zlttbots ENVIRONMENT=dev bash scripts/meta-clean.sh

# Staging cleanup
CONFIRM=true PROJECT_NAME=zlttbots ENVIRONMENT=staging bash scripts/meta-clean.sh

# Prod cleanup (explicit double-ack)
CONFIRM=true FORCE_PROD=true PROJECT_NAME=zlttbots ENVIRONMENT=prod bash scripts/meta-clean.sh
```

## Notes

- If data reset is required, do it through service-level commands/migrations, not direct filesystem deletion.
- Keep cleanup scoped to project resources to avoid multi-tenant host impact.
- Run CI checks after cleanup to validate health before redeploy.
