#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ECOSYSTEM_CONFIG="$REPO_ROOT/ecosystem.config.js"
LOG_DIR="$REPO_ROOT/logs/node"
PID_DIR="$LOG_DIR/pids"

mkdir -p "$LOG_DIR" "$PID_DIR"

PM2_CMD=""

run_npm() {
  npm "$@" || (
    unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY npm_config_http_proxy npm_config_https_proxy
    npm "$@"
  )
}

start_with_nohup() {
  echo "PM2 unavailable. Falling back to nohup background processes."
  local failures=0

  while IFS= read -r package_file; do
    service_dir="$(dirname "$package_file")"
    service_name="$(basename "$service_dir")"
    pid_file="$PID_DIR/$service_name.pid"
    out_log="$LOG_DIR/$service_name.out.log"

    if [ -f "$pid_file" ]; then
      existing_pid="$(cat "$pid_file")"
      if kill -0 "$existing_pid" >/dev/null 2>&1; then
        echo "Service $service_name is already running with PID $existing_pid"
        continue
      fi
      rm -f "$pid_file"
    fi

    echo "Starting $service_name with nohup..."
    nohup bash -lc "cd '$service_dir' && env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY -u npm_config_http_proxy -u npm_config_https_proxy npm run start" >"$out_log" 2>&1 &
    new_pid=$!

    sleep 2

    if kill -0 "$new_pid" >/dev/null 2>&1; then
      echo "$new_pid" >"$pid_file"
      echo "Started $service_name (PID $new_pid, log: $out_log)"
    else
      failures=$((failures + 1))
      echo "ERROR: $service_name failed to stay running. Recent log output:"
      tail -n 20 "$out_log" || true
    fi
  done < <(find "$REPO_ROOT/services" -mindepth 2 -maxdepth 2 -name package.json | sort)

  echo ""
  echo "================================="
  echo "Node Services Started via nohup"
  echo "PID files: $PID_DIR"
  echo "Logs: $LOG_DIR"
  echo "================================="

  if [ "$failures" -gt 0 ]; then
    echo "ERROR: $failures service(s) failed to start via nohup."
    exit 1
  fi
}

resolve_pm2() {
  if command -v pm2 >/dev/null 2>&1; then
    PM2_CMD="pm2"
    return
  fi

  if [ -x "$REPO_ROOT/node_modules/.bin/pm2" ]; then
    PM2_CMD="$REPO_ROOT/node_modules/.bin/pm2"
    return
  fi

  echo "PM2 not found. Attempting global install..."
  if run_npm install -g pm2; then
    if command -v pm2 >/dev/null 2>&1; then
      PM2_CMD="pm2"
      return
    fi
  fi

  PM2_CMD=""
}

echo "================================="
echo "Starting Node Services"
echo "Repo: $REPO_ROOT"
echo "================================="

if [ ! -f "$ECOSYSTEM_CONFIG" ]; then
  echo "ERROR: ecosystem config not found at $ECOSYSTEM_CONFIG"
  exit 1
fi

if [ "${SKIP_DEP_INSTALL:-0}" = "1" ]; then
  echo "Skipping dependency installation (SKIP_DEP_INSTALL=1)."
else
  echo "Installing npm dependencies for Node services..."
  while IFS= read -r package_file; do
    service_dir="$(dirname "$package_file")"
    echo "Installing dependencies -> $(basename "$service_dir")"
    pushd "$service_dir" >/dev/null

    if [ -f package-lock.json ]; then
      run_npm ci
    else
      run_npm install
    fi

    popd >/dev/null
  done < <(find "$REPO_ROOT/services" -mindepth 2 -maxdepth 2 -name package.json | sort)
fi

resolve_pm2

if [ -n "$PM2_CMD" ]; then
  echo "Starting PM2 processes from $ECOSYSTEM_CONFIG"
  "$PM2_CMD" start "$ECOSYSTEM_CONFIG"
  "$PM2_CMD" save
  "$PM2_CMD" list

  echo ""
  echo "================================="
  echo "Node Services Started via PM2"
  echo "PM2 logs: $PM2_CMD logs"
  echo "================================="
else
  start_with_nohup
fi
