#!/usr/bin/env bash

# Shared configuration for zTTato-managed Node.js services.

if [[ -z "${ZTTATO_ROOT:-}" ]]; then
  ZTTATO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

ZTTATO_NODE_SERVICES_ROOT="$ZTTATO_ROOT/services"
ZTTATO_NODE_LOG_DIR="$ZTTATO_ROOT/logs/node"
ZTTATO_NODE_PID_DIR="$ZTTATO_ROOT/pids/node"

zttato_node_discover_services() {
  find "$ZTTATO_NODE_SERVICES_ROOT" -mindepth 1 -maxdepth 2 -name package.json -print \
    | sed "s#^$ZTTATO_NODE_SERVICES_ROOT/##" \
    | sed 's#/package.json$##' \
    | sort
}

mapfile -t ZTTATO_NODE_SERVICES < <(zttato_node_discover_services)

zttato_node_print_service_list() {
  printf '%s\n' "${ZTTATO_NODE_SERVICES[@]}"
}

zttato_node_service_dir() {
  printf '%s/%s\n' "$ZTTATO_NODE_SERVICES_ROOT" "$1"
}

zttato_node_service_package() {
  printf '%s/package.json\n' "$(zttato_node_service_dir "$1")"
}

zttato_node_prepare_runtime_dirs() {
  mkdir -p "$ZTTATO_NODE_LOG_DIR" "$ZTTATO_NODE_PID_DIR"
}

zttato_node_has_package() {
  [[ -f "$(zttato_node_service_package "$1")" ]]
}
