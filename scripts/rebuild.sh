#!/usr/bin/env bash
set -euo pipefail

echo "================================="
echo "[REBUILD] Clean + Reinstall Workflow for zlttbots"
echo "================================="

# -------------------------------
# Phase 1: Clean
# -------------------------------
echo ">>> Phase 1: Cleaning environment..."

# Stop and remove all containers safely
if [ -n "$(docker ps -q)" ]; then
  docker stop $(docker ps -q)
fi

if [ -n "$(docker ps -aq)" ]; then
  docker rm -f $(docker ps -aq)
fi

# Prune networks, volumes, images
docker network prune -f
docker volume prune -f
docker image prune -af

# Remove old auto-generated network if present
if docker network ls --format "{{.Name}}" | grep -q "^zlttbots_zlttbots-net$"; then
  echo ">>> Removing old network zlttbots_zlttbots-net"
  docker network rm zlttbots_zlttbots-net || true
fi

# Ensure correct network exists
if ! docker network ls --format "{{.Name}}" | grep -q "^zlttbots-net$"; then
  echo ">>> Creating network zlttbots-net"
  docker network create zlttbots-net
fi

# Clear Node caches for all services
for svc in services/*; do
  if [ -f "$svc/package.json" ]; then
    echo " -> Cleaning $svc"
    (
      cd "$svc"
      rm -rf node_modules || true
      find . -name "node_modules" -type d -prune -exec rm -rf {} + || true
      npm cache clean --force || true
    )
  fi
done

# Extra: wipe npm cache directory if ENOTEMPTY occurs
rm -rf ~/.npm/_cacache || true

# Reset local data directories if present
rm -rf ./data/postgres/* || true
rm -rf ./data/redis/* || true

echo ">>> Phase 1 complete"
echo "================================="

# -------------------------------
# Phase 2: Reinstall
# -------------------------------
echo ">>> Phase 2: Reinstalling zlttbots platform..."

bash scripts/start-zlttbots.sh --core
bash scripts/zlttbots-manager.sh install
bash scripts/zlttbots-manager.sh status

echo ">>> Phase 2 complete"
echo "================================="

# -------------------------------
# Phase 3: Auto-Restart Loop
# -------------------------------
echo ">>> Phase 3: Checking for Restarting containers..."
for c in $(docker ps --filter "status=restarting" --format "{{.Names}}"); do
  echo " -> Attempting restart for $c"
  for i in 1 2 3; do
    docker restart "$c" || true
    sleep 5
    status=$(docker inspect --format='{{.State.Status}}' "$c")
    if [ "$status" = "running" ]; then
      echo "    $c recovered after $i attempt(s)"
      break
    fi
  done
done

# -------------------------------
# Phase 4: Status Summary
# -------------------------------
echo ">>> Phase 4: Docker service summary"
echo "================================="

docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" \
  | grep -E "zlttbots|zttato-" \
  | awk 'NR==1 {print; next}
         /healthy/ {print "\033[32m" $0 "\033[0m"}
         /unhealthy/ {print "\033[31m" $0 "\033[0m"}
         /Restarting/ {print "\033[33m" $0 "\033[0m"}
         !/healthy|unhealthy|Restarting/ {print $0}'

echo "================================="
echo "[REBUILD] Workflow complete"
echo "================================="
