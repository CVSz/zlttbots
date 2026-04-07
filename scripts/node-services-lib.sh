#!/usr/bin/env bash

# Shared configuration for zlttbots-managed Node.js services.

if [[ -z "${ZLTTBOTS_ROOT:-}" ]]; then
  ZLTTBOTS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

ZLTTBOTS_NODE_SERVICES_ROOT="$ZLTTBOTS_ROOT/services"
ZLTTBOTS_NODE_LOG_DIR="$ZLTTBOTS_ROOT/logs/node"
ZLTTBOTS_NODE_PID_DIR="$ZLTTBOTS_ROOT/pids/node"

zlttbots_node_discover_services() {
  find "$ZLTTBOTS_NODE_SERVICES_ROOT" -mindepth 1 -maxdepth 2 -name package.json -print \
    | sed "s#^$ZLTTBOTS_NODE_SERVICES_ROOT/##" \
    | sed 's#/package.json$##' \
    | sort
}

mapfile -t ZLTTBOTS_NODE_SERVICES < <(zlttbots_node_discover_services)

zlttbots_node_print_service_list() {
  printf '%s\n' "${ZLTTBOTS_NODE_SERVICES[@]}"
}

zlttbots_node_service_dir() {
  printf '%s/%s\n' "$ZLTTBOTS_NODE_SERVICES_ROOT" "$1"
}

zlttbots_node_service_package() {
  printf '%s/package.json\n' "$(zlttbots_node_service_dir "$1")"
}

zlttbots_node_prepare_runtime_dirs() {
  mkdir -p "$ZLTTBOTS_NODE_LOG_DIR" "$ZLTTBOTS_NODE_PID_DIR"
}

zlttbots_node_has_package() {
  [[ -f "$(zlttbots_node_service_package "$1")" ]]
}
