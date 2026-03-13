#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "--------------------------------"
echo "Repository Validation"
echo "--------------------------------"

mapfile -t dockerfiles < <(find "$ROOT" -type f -name Dockerfile -not -path '*/node_modules/*' | sort)
mapfile -t package_jsons < <(find "$ROOT/services" -type f -name package.json -not -path '*/node_modules/*' | sort)
mapfile -t requirements_files < <(find "$ROOT/services" -type f -name requirements.txt | sort)
mapfile -t shell_scripts < <(find "$ROOT" -type f -name '*.sh' -not -path '*/node_modules/*' | sort)
mapfile -t python_files < <(find "$ROOT/services" -type f -name '*.py' -not -path '*/__pycache__/*' | sort)
mapfile -t kubernetes_manifests < <(find "$ROOT/infrastructure/k8s" -type f -name '*.yaml' | sort)

echo ""
echo "Dockerfiles (${#dockerfiles[@]}):"
printf '%s\n' "${dockerfiles[@]}"

echo ""
echo "Node services (${#package_jsons[@]}):"
printf '%s\n' "${package_jsons[@]}"

echo ""
echo "Python services (${#requirements_files[@]}):"
printf '%s\n' "${requirements_files[@]}"

echo ""
echo "Shell scripts (${#shell_scripts[@]}):"
printf '%s\n' "${shell_scripts[@]}"

echo ""
echo "Kubernetes manifests (${#kubernetes_manifests[@]}):"
printf '%s\n' "${kubernetes_manifests[@]}"

echo ""
echo "Running checks..."

if ((${#shell_scripts[@]} > 0)); then
  while IFS= read -r script; do
    bash -n "$script"
  done < <(printf '%s\n' "${shell_scripts[@]}")
  echo "✅ Shell syntax check passed (${#shell_scripts[@]} files)"
fi

if ((${#python_files[@]} > 0)); then
  while IFS= read -r pyfile; do
    python -m py_compile "$pyfile"
  done < <(printf '%s\n' "${python_files[@]}")
  echo "✅ Python syntax check passed (${#python_files[@]} files)"
fi

if ((${#package_jsons[@]} > 0)); then
  while IFS= read -r package_json; do
    python -m json.tool "$package_json" >/dev/null
  done < <(printf '%s\n' "${package_jsons[@]}")
  echo "✅ package.json validation passed (${#package_jsons[@]} files)"
fi

echo ""
echo "Validation completed successfully."
