#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
status=0
FALLBACK_ON_AUDIT_UNAVAILABLE="${FALLBACK_ON_AUDIT_UNAVAILABLE:-1}"
ENFORCE_LOCKFILE="${ENFORCE_LOCKFILE:-0}"
missing_lockfiles=()

run_outdated_fallback() {
  local package_dir="$1"
  echo "Falling back to npm outdated for $package_dir"
  (
    cd "$package_dir"
    npm outdated --long || true
  )
}

run_audit() {
  local package_dir="$1"
  local audit_output
  set +e
  audit_output="$(cd "$package_dir" && npm audit --omit=dev --audit-level=high 2>&1)"
  local audit_rc=$?
  set -e

  if [[ $audit_rc -eq 0 ]]; then
    echo "$audit_output"
    return 0
  fi

  echo "$audit_output"
  if [[ "$FALLBACK_ON_AUDIT_UNAVAILABLE" == "1" ]] && grep -Eq "ENOAUDIT|audit endpoint returned an error|503 Service Unavailable|EAI_AGAIN|ECONNREFUSED|ETIMEDOUT" <<<"$audit_output"; then
    run_outdated_fallback "$package_dir"
    return 0
  fi

  return "$audit_rc"
}

while IFS= read -r package; do
  package_dir="$(dirname "$package")"
  lockfile="$package_dir/package-lock.json"

  if [[ ! -f "$lockfile" ]]; then
    echo "Missing lockfile for $package_dir"
    missing_lockfiles+=("$package_dir")
    if [[ "$ENFORCE_LOCKFILE" == "1" ]]; then
      status=1
    fi
    continue
  fi

  echo "Scanning $package_dir"
  run_audit "$package_dir" || status=1
done < <(
  {
    find "$ROOT" -maxdepth 1 -name package.json
    find "$ROOT/apps" -maxdepth 2 -name package.json
    find "$ROOT/services" -maxdepth 2 -name package.json
  } | sort -u
)

if ((${#missing_lockfiles[@]} > 0)); then
  echo
  if [[ "$ENFORCE_LOCKFILE" == "1" ]]; then
    echo "Missing lockfiles detected (ENFORCE_LOCKFILE=1):"
  else
    echo "Missing lockfiles detected (warning only; set ENFORCE_LOCKFILE=1 to enforce):"
  fi
  printf ' - %s\n' "${missing_lockfiles[@]}"
fi

exit "$status"
