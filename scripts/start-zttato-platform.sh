#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

log(){ printf '[start] %s\n' "$*"; }
fail(){ printf 'ERROR: %s\n' "$*" >&2; exit 1; }

readonly CORE_SERVICES=(
  postgres
  redis
  viral-predictor
  market-crawler
  arbitrage-engine
  gpu-renderer
  crawler-worker
  arbitrage-worker
  renderer-worker
  nginx
)

compose_cmd(){
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    fail "docker compose or docker-compose is required"
  fi
}

is_snapshot_cache_error(){
  local log_file="$1"
  grep -Eq 'failed to prepare extraction snapshot|parent snapshot .* does not exist' "$log_file"
}

compose_up_with_recovery(){
  local -a compose_args=("$@")
  local tmp_log
  tmp_log="$(mktemp)"

  set +e
  compose_cmd up -d --build --remove-orphans "${compose_args[@]}" 2>&1 | tee "$tmp_log"
  local up_status=${PIPESTATUS[0]}
  set -e

  if [[ $up_status -eq 0 ]]; then
    rm -f "$tmp_log"
    return 0
  fi

  if is_snapshot_cache_error "$tmp_log"; then
    log "Detected corrupted Docker BuildKit snapshot cache; pruning builder cache and retrying once"
    docker builder prune -af >/dev/null
    compose_cmd up -d --build --remove-orphans "${compose_args[@]}"
    rm -f "$tmp_log"
    return 0
  fi

  rm -f "$tmp_log"
  return "$up_status"
}

ensure_env(){
  [[ -f .env ]] || bash "$ROOT_DIR/scripts/install-zlttbots.sh"
}

print_usage(){
  cat <<'USAGE'
Usage: start-zlttbots.sh [--core|--full]

Modes:
  --core  Start only core runtime services to reduce build/storage usage.
  --full  Start the full platform stack (default).

Environment override:
  ZTTATO_STACK_MODE=core|full
USAGE
}

STACK_MODE=""

resolve_mode(){
  STACK_MODE="${ZTTATO_STACK_MODE:-full}"

  while (($#)); do
    case "$1" in
      --core) STACK_MODE="core" ;;
      --full) STACK_MODE="full" ;;
      -h|--help)
        print_usage
        exit 0
        ;;
      *)
        fail "unknown argument: $1 (use --help)"
        ;;
    esac
    shift
  done

  case "$STACK_MODE" in
    core|full) ;;
    *) fail "invalid ZTTATO_STACK_MODE '$STACK_MODE' (allowed: core|full)" ;;
  esac
}

smoke_check(){
  local url="$1"
  local name="$2"
  if curl -fsS "$url" >/dev/null 2>&1; then
    log "$name OK"
  else
    log "$name not ready yet"
  fi
}

resolve_mode "$@"
ensure_env
log "Validating compose configuration"
compose_cmd config >/dev/null
if [[ "$STACK_MODE" == "core" ]]; then
  log "Building and starting CORE compose stack (reduced footprint)"
  compose_up_with_recovery "${CORE_SERVICES[@]}"
else
  log "Building and starting FULL compose stack"
  compose_up_with_recovery
fi
log "Current compose status"
compose_cmd ps

sleep 3
smoke_check "http://localhost/" "gateway"
smoke_check "http://localhost:9100/docs" "viral-predictor"
smoke_check "http://localhost:9400/docs" "market-crawler"
smoke_check "http://localhost:9500/docs" "arbitrage-engine"
smoke_check "http://localhost:9300/docs" "gpu-renderer"

log "zTTato platform start completed"
