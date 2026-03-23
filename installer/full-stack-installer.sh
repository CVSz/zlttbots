#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_TEMPLATE="$ROOT_DIR/configs/env/full-stack.env.example"
ENV_FILE="$ROOT_DIR/.env"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"

LOG_PREFIX="[full-stack-installer]"

log() {
  printf '%s %s\n' "$LOG_PREFIX" "$*"
}

fail() {
  printf '%s ERROR: %s\n' "$LOG_PREFIX" "$*" >&2
  exit 1
}

usage() {
  cat <<'USAGE'
Usage:
  bash installer/full-stack-installer.sh <command>

Commands:
  prereq      Validate host requirements for full-stack installation.
  config      Create .env from full-stack template if it does not exist.
  starter     Build and start the Docker Compose stack.
  deploy      Install dependencies, configure environment, and start stack.
  verify      Run health checks for gateway and critical services.
  stop        Stop the stack (preserve volumes).
  uninstall   Stop stack and delete persistent volumes.
  help        Show this help message.

Examples:
  bash installer/full-stack-installer.sh deploy
  bash installer/full-stack-installer.sh verify
USAGE
}

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || fail "Missing required command: $cmd"
}

compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    fail "Docker Compose is required. Install Docker Compose v2 plugin or docker-compose."
  fi
}

check_prereqs() {
  require_cmd bash
  require_cmd docker
  require_cmd curl
  require_cmd python3
  require_cmd git

  if ! docker info >/dev/null 2>&1; then
    fail "Docker daemon is not reachable. Start Docker and rerun."
  fi

  [[ -f "$COMPOSE_FILE" ]] || fail "Missing docker-compose.yml at repository root."
  [[ -f "$ENV_TEMPLATE" ]] || fail "Missing template env file: $ENV_TEMPLATE"

  log "Prerequisite validation passed."
}

create_env_if_needed() {
  if [[ -f "$ENV_FILE" ]]; then
    log ".env already exists; keeping existing values."
    return
  fi

  cp "$ENV_TEMPLATE" "$ENV_FILE"
  log "Created .env from template: configs/env/full-stack.env.example"
  log "Edit .env before production deployment, especially secrets and external API endpoints."
}

validate_env_security() {
  if [[ ! -f "$ENV_FILE" ]]; then
    fail "Missing .env. Run 'config' command first."
  fi

  if rg -q '^AFFILIATE_WEBHOOK_SECRET=change-me$' "$ENV_FILE"; then
    fail "AFFILIATE_WEBHOOK_SECRET is using default 'change-me'. Update .env before deploy."
  fi

  if rg -q '^PLATFORM_API_KEY=$' "$ENV_FILE"; then
    log "PLATFORM_API_KEY is empty; external execution-engine integrations may fail until configured."
  fi

  log "Environment validation passed."
}

start_stack() {
  log "Validating compose configuration."
  compose_cmd config >/dev/null

  log "Building and starting the full stack."
  compose_cmd up -d --build --remove-orphans

  log "Current stack status."
  compose_cmd ps
}

health_probe() {
  local name="$1"
  local url="$2"

  if curl --fail --silent --show-error --max-time 10 "$url" >/dev/null; then
    log "Health OK: $name ($url)"
  else
    fail "Health FAILED: $name ($url)"
  fi
}

verify_stack() {
  health_probe "gateway" "http://localhost/"
  health_probe "viral-predictor" "http://localhost:9100/healthz"
  health_probe "market-crawler" "http://localhost:9400/healthz"
  health_probe "arbitrage-engine" "http://localhost:9500/healthz"
  health_probe "gpu-renderer" "http://localhost:9300/healthz"
  log "All critical health probes passed."
}

stop_stack() {
  log "Stopping stack (volumes preserved)."
  compose_cmd down
}

uninstall_stack() {
  log "Stopping stack and deleting volumes."
  compose_cmd down -v --remove-orphans
}

run_deploy() {
  check_prereqs
  create_env_if_needed
  validate_env_security
  start_stack
  verify_stack
  log "Full-stack deployment completed successfully."
}

main() {
  local cmd="${1:-help}"

  case "$cmd" in
    prereq)
      check_prereqs
      ;;
    config)
      check_prereqs
      create_env_if_needed
      ;;
    starter)
      check_prereqs
      validate_env_security
      start_stack
      ;;
    deploy)
      run_deploy
      ;;
    verify)
      verify_stack
      ;;
    stop)
      stop_stack
      ;;
    uninstall)
      uninstall_stack
      ;;
    help|-h|--help)
      usage
      ;;
    *)
      usage
      fail "Unknown command: $cmd"
      ;;
  esac
}

main "$@"
