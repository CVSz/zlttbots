#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

log(){ printf '[deploy] %s\n' "$*"; }

log "Installing prerequisites and generating .env when needed"
bash "$ROOT_DIR/scripts/install-zlttbots.sh"

log "Upgrading runtime assets"
bash "$ROOT_DIR/scripts/upgrade-zlttbots.sh"

log "Starting stack and running smoke checks"
bash "$ROOT_DIR/scripts/start-zlttbots.sh"

log "Deployment completed"
