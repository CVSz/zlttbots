# path: scripts/generate-devops-pack.sh
#!/usr/bin/env bash
#
# Generator: DevOps script pack for zlttbots
# Creates production helper scripts under infrastructure/scripts
#
# Usage:
#   bash scripts/generate-devops-pack.sh

set -Eeuo pipefail

ROOT="$(pwd)"
TARGET="$ROOT/infrastructure/scripts"

echo "--------------------------------"
echo "DevOps Script Generator"
echo "Root: $ROOT"
echo "Target: $TARGET"
echo "--------------------------------"

mkdir -p "$TARGET"

############################################
# bootstrap-platform.sh
############################################

cat > "$TARGET/bootstrap-platform.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "Bootstrapping platform..."

echo "Fixing shell permissions..."
find "$ROOT" -type f -name "*.sh" -exec chmod +x {} \;

echo ""
echo "Installing Node dependencies..."

NODE_PKGS=$(find "$ROOT/services" -maxdepth 2 -name package.json)

for pkg in $NODE_PKGS
do
  dir=$(dirname "$pkg")
  echo "npm install -> $dir"
  (cd "$dir" && npm install)
done

echo ""
echo "Installing Python dependencies..."

PY_PKGS=$(find "$ROOT/services" -maxdepth 2 -name requirements.txt)

for req in $PY_PKGS
do
  dir=$(dirname "$req")
  echo "pip install -> $dir"
  (cd "$dir" && pip install -r requirements.txt)
done

echo ""
echo "Starting Docker compose..."

cd "$ROOT"
docker compose up -d

echo "Bootstrap completed."
EOF

############################################
# build-all-images.sh
############################################

cat > "$TARGET/build-all-images.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "Building all Docker images..."

DOCKERFILES=$(find "$ROOT/services" -name Dockerfile)

for df in $DOCKERFILES
do
  dir=$(dirname "$df")
  service=$(basename "$(dirname "$dir")")

  echo "Building image: $service"
  docker build -t zlttbots/$service "$dir"
done

echo "Build complete."
EOF

############################################
# start-dev-cluster.sh
############################################

cat > "$TARGET/start-dev-cluster.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "Starting development cluster..."

cd "$ROOT"
docker compose up -d

echo "Cluster running."
EOF

############################################
# deploy-kubernetes.sh
############################################

cat > "$TARGET/deploy-kubernetes.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "Deploying Kubernetes resources..."

kubectl apply -f "$ROOT/infrastructure/k8s/config"
kubectl apply -f "$ROOT/infrastructure/k8s/base"
kubectl apply -f "$ROOT/infrastructure/k8s/services"
kubectl apply -f "$ROOT/infrastructure/k8s/deployments"
kubectl apply -f "$ROOT/infrastructure/k8s/autoscale"
kubectl apply -f "$ROOT/infrastructure/k8s/ingress"

echo "Deployment complete."
EOF

############################################
# validate-repo.sh
############################################

cat > "$TARGET/validate-repo.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "--------------------------------"
echo "Repository Validation"
echo "--------------------------------"

echo ""
echo "Dockerfiles:"
find "$ROOT" -name Dockerfile

echo ""
echo "Node services:"
find "$ROOT/services" -name package.json

echo ""
echo "Python services:"
find "$ROOT/services" -name requirements.txt

echo ""
echo "Shell scripts:"
find "$ROOT" -name "*.sh"

echo ""
echo "Kubernetes manifests:"
find "$ROOT/infrastructure/k8s" -name "*.yaml"

echo ""
echo "Validation completed."
EOF

############################################
# set permissions
############################################

chmod +x "$TARGET"/*.sh

echo ""
echo "--------------------------------"
echo "DevOps scripts generated:"
ls -1 "$TARGET"
echo "--------------------------------"
