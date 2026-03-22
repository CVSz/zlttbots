#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

command -v slither >/dev/null 2>&1 || { echo "slither is required" >&2; exit 1; }
command -v echidna-test >/dev/null 2>&1 || { echo "echidna-test is required" >&2; exit 1; }
command -v scribble >/dev/null 2>&1 || { echo "scribble is required" >&2; exit 1; }

slither .
echidna-test .
scribble ./*.sol --output-mode flat --output-dir ./build/scribble
