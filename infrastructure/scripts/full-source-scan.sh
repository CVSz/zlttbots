#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

echo "=== ZLTTBOTS Full Source Scan ==="
echo "Repository: $ROOT_DIR"

echo
printf "[1/4] Python syntax scan... "
PY_FILES="$(rg --files -g '*.py')"
if [[ -n "$PY_FILES" ]]; then
  python -m py_compile $PY_FILES
fi
echo "OK"

echo
printf "[2/4] JavaScript syntax scan (.js)... "
JS_FILES="$(rg --files -g '*.js')"
if [[ -n "$JS_FILES" ]]; then
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    node --check "$f" >/dev/null
  done <<< "$JS_FILES"
fi
echo "OK"

echo
printf "[3/4] JSX inventory... "
JSX_COUNT="$(rg --files -g '*.jsx' | wc -l | tr -d ' ')"
echo "$JSX_COUNT file(s) detected"
if [[ "$JSX_COUNT" -gt 0 ]]; then
  echo "      Note: JSX syntax requires a JSX-aware parser (e.g., Vite/Next/Babel build) and is validated in service-level build/test pipelines."
fi

echo
printf "[4/4] Pytest suite...\n"
pytest -q

echo
echo "All configured checks completed."
