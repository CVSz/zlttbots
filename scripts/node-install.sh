# scripts/node-install.sh
#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

############################################
# colors
############################################

GREEN="\033[32m"
NC="\033[0m"

log(){
echo -e "${GREEN}[zTTato]${NC} $*"
}

############################################
# install node services
############################################

log "Installing Node services"

for svc in "$ROOT/services/"*
do

if [ ! -f "$svc/package.json" ]; then
continue
fi

NAME=$(basename "$svc")

log "npm install -> $NAME"

(
cd "$svc"

if [ -f package-lock.json ]; then
npm ci --silent
else
npm install --silent
fi

)

done

log "Node dependencies installed"
