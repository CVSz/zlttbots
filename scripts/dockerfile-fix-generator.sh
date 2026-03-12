# path: scripts/dockerfile-fix-generator.sh
#!/usr/bin/env bash
#
# Dockerfile Fix Generator
# Scans services for Python Dockerfiles that reference requirements.txt
# and ensures build context + Dockerfile location are correct.
#
# Actions:
# 1. Detect services with docker/Dockerfile + requirements.txt in parent
# 2. Move Dockerfile to service root (best practice)
# 3. Patch docker-compose.yml build context if needed
# 4. Print rebuild instructions
#
# Usage:
#   bash scripts/dockerfile-fix-generator.sh

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICES_DIR="$ROOT/services"
COMPOSE_FILE="$ROOT/docker-compose.yml"

echo "========================================"
echo "Dockerfile Fix Generator"
echo "Root: $ROOT"
echo "========================================"

FIXED=0

for svc in "$SERVICES_DIR"/*; do
  [ -d "$svc" ] || continue

  NAME=$(basename "$svc")

  DOCKER_DIR="$svc/docker"
  DOCKERFILE_IN_DOCKER="$DOCKER_DIR/Dockerfile"
  REQUIREMENTS="$svc/requirements.txt"
  TARGET_DOCKERFILE="$svc/Dockerfile"

  if [[ -f "$DOCKERFILE_IN_DOCKER" && -f "$REQUIREMENTS" ]]; then
    echo ""
    echo "Fixing service: $NAME"

    # Move Dockerfile to service root
    if [[ ! -f "$TARGET_DOCKERFILE" ]]; then
      mv "$DOCKERFILE_IN_DOCKER" "$TARGET_DOCKERFILE"
      echo "Moved Dockerfile -> $TARGET_DOCKERFILE"
    fi

    # Clean docker directory if empty
    rmdir "$DOCKER_DIR" 2>/dev/null || true

    # Rewrite Dockerfile
    cat > "$TARGET_DOCKERFILE" <<'EOF'
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

CMD ["python","src/main.py"]
EOF

    echo "Rewritten Dockerfile"

    ((FIXED++))
  fi
done

echo ""
echo "========================================"
echo "Dockerfile fixes applied: $FIXED"
echo "========================================"

########################################
# Patch docker-compose build contexts
########################################

if [[ -f "$COMPOSE_FILE" ]]; then

  echo ""
  echo "Checking docker-compose.yml build contexts..."

  for svc in "$SERVICES_DIR"/*; do
    NAME=$(basename "$svc")

    if grep -q "$NAME/docker" "$COMPOSE_FILE"; then
      sed -i "s|$NAME/docker|$NAME|g" "$COMPOSE_FILE"
      echo "Patched compose context -> $NAME"
    fi
  done

fi

########################################
# Summary
########################################

echo ""
echo "Next steps:"
echo ""
echo "1. rebuild containers:"
echo ""
echo "docker compose build --no-cache"
echo ""
echo "2. start platform:"
echo ""
echo "./start-zttato.sh"
echo ""
echo "========================================"
