#!/usr/bin/env bash
set -euo pipefail

# zTTato adaptation of requested ZEAZ single-file installer.
# This script generates a production-oriented stack at /opt/zttato-platform.

DOMAIN=""
CERT_EMAIL=""
APP_DIR="/opt/zttato-platform"
EXPORT_ZIP="false"
BUILD_FULL_PACK="true"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --domain) DOMAIN="${2:-}"; shift 2 ;;
    --cert-email) CERT_EMAIL="${2:-}"; shift 2 ;;
    --export-zip) EXPORT_ZIP="true"; shift 1 ;;
    --skip-full-pack) BUILD_FULL_PACK="false"; shift 1 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$DOMAIN" ]]; then
  echo "Usage: sudo bash installer/zttato-ai-full-stack-installer.sh --domain your-domain [--cert-email admin@your-domain] [--export-zip] [--skip-full-pack]"
  exit 1
fi

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root."
  exit 1
fi

log() { echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] $*"; }

log "[1/8] Preflight checks"
free -g | awk '/Mem:/ {if ($2 < 8) {print "Need >=8GB RAM"; exit 1}}'
df -BG / | awk 'NR==2 {gsub("G","",$4); if ($4 < 50) {print "Need >=50GB free disk"; exit 1}}'

log "[2/8] Install dependencies"
export DEBIAN_FRONTEND=noninteractive
apt update
apt install -y docker.io docker-compose-plugin curl jq openssl ca-certificates ufw certbot zip
systemctl enable docker
systemctl start docker

log "[3/8] Generate project files"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"/{api,worker,agent,control,analytics,infra,panels/{admin,user,devops},backup,monitor,logs,db,certs,prometheus}
if [[ "$BUILD_FULL_PACK" == "true" ]]; then
  mkdir -p "$APP_DIR"/{k8s,frontend/src}
fi

DB_PASS="$(openssl rand -hex 32)"
REDIS_PASS="$(openssl rand -hex 32)"
JWT_SECRET_CURRENT="$(openssl rand -hex 48)"
JWT_SECRET_PREVIOUS=""
KAFKA_USER="zttato_app"
KAFKA_PASS="$(openssl rand -hex 24)"
ADMIN_PASS="$(openssl rand -base64 18)"
API_HMAC_SECRET="$(openssl rand -hex 48)"

cat > "$APP_DIR/.env" <<ENVFILE
DOMAIN=${DOMAIN}
DB_PASS=${DB_PASS}
REDIS_PASS=${REDIS_PASS}
TRUST_PROXY=true
REAL_IP_HEADER=X-Forwarded-For
DATABASE_URL=postgresql://zttato:${DB_PASS}@db:5432/zttato
JWT_SECRET=${JWT_SECRET_CURRENT}
JWT_SECRET_CURRENT=${JWT_SECRET_CURRENT}
JWT_SECRET_PREVIOUS=${JWT_SECRET_PREVIOUS}
REDIS_URL=redis://:${REDIS_PASS}@redis:6379/0
KAFKA_BROKER=kafka:9092
KAFKA_SECURITY_PROTOCOL=SASL_PLAINTEXT
KAFKA_SASL_MECHANISM=PLAIN
KAFKA_USERNAME=${KAFKA_USER}
KAFKA_PASSWORD=${KAFKA_PASS}
ENABLE_AGENTS=true
MAX_DAILY_SPEND=500
ENVFILE
chmod 600 "$APP_DIR/.env"

cat > "$APP_DIR/api/api.env" <<ENVFILE
DATABASE_URL=postgresql://zttato:${DB_PASS}@db:5432/zttato
JWT_SECRET=${JWT_SECRET_CURRENT}
JWT_SECRET_CURRENT=${JWT_SECRET_CURRENT}
JWT_SECRET_PREVIOUS=${JWT_SECRET_PREVIOUS}
REDIS_URL=redis://:${REDIS_PASS}@redis:6379/0
TRUST_PROXY=true
REAL_IP_HEADER=X-Forwarded-For
KAFKA_BROKER=kafka:9092
KAFKA_SECURITY_PROTOCOL=SASL_PLAINTEXT
KAFKA_SASL_MECHANISM=PLAIN
KAFKA_USERNAME=${KAFKA_USER}
KAFKA_PASSWORD=${KAFKA_PASS}
CORS_ORIGINS=https://${DOMAIN}
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
QDRANT_HOST=qdrant
QDRANT_PORT=6333
MEMORY_MODEL=all-MiniLM-L6-v2
API_HMAC_SECRET=${API_HMAC_SECRET}
STRIPE_SECRET=
STRIPE_WEBHOOK_SECRET=
ENVFILE
chmod 600 "$APP_DIR/api/api.env"

cat > "$APP_DIR/worker/worker.env" <<ENVFILE
DATABASE_URL=postgresql://zttato:${DB_PASS}@db:5432/zttato
KAFKA_BROKER=kafka:9092
KAFKA_SECURITY_PROTOCOL=SASL_PLAINTEXT
KAFKA_SASL_MECHANISM=PLAIN
KAFKA_USERNAME=${KAFKA_USER}
KAFKA_PASSWORD=${KAFKA_PASS}
ENVFILE
chmod 600 "$APP_DIR/worker/worker.env"

if [[ -n "$CERT_EMAIL" && "$DOMAIN" != "localhost" && "$DOMAIN" != *.local ]]; then
  log "Attempting Let's Encrypt certificate for ${DOMAIN}"
  OCCUPYING_CONTAINERS="$(docker ps --filter publish=80 --format '{{.ID}}')"
  if [[ -n "${OCCUPYING_CONTAINERS}" ]]; then
    log "Stopping containers bound to port 80 for certbot standalone challenge"
    docker stop ${OCCUPYING_CONTAINERS} >/dev/null
  fi
  if certbot certonly --standalone --non-interactive --agree-tos -m "$CERT_EMAIL" -d "$DOMAIN"; then
    cp "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" "$APP_DIR/certs/tls.crt"
    cp "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" "$APP_DIR/certs/tls.key"
    chmod 600 "$APP_DIR/certs/tls.key"
    log "Let's Encrypt certificate issued for ${DOMAIN}"
  else
    log "Let's Encrypt failed, falling back to self-signed certificate"
    openssl req -x509 -nodes -newkey rsa:2048 \
      -keyout "$APP_DIR/certs/tls.key" \
      -out "$APP_DIR/certs/tls.crt" \
      -days 365 \
      -subj "/CN=${DOMAIN}"
    chmod 600 "$APP_DIR/certs/tls.key"
  fi
else
  log "Using self-signed certificate (provide --cert-email for Let's Encrypt on public domains)"
  openssl req -x509 -nodes -newkey rsa:2048 \
    -keyout "$APP_DIR/certs/tls.key" \
    -out "$APP_DIR/certs/tls.crt" \
    -days 365 \
    -subj "/CN=${DOMAIN}"
  chmod 600 "$APP_DIR/certs/tls.key"
fi

cat > "$APP_DIR/control/requirements.txt" <<'REQ'
fastapi==0.110.0
uvicorn==0.29.0
REQ

cat > "$APP_DIR/control/Dockerfile" <<'DOCKER'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8080"]
DOCKER

cat > "$APP_DIR/control/main.py" <<'PYCODE'
from fastapi import FastAPI
import os

app = FastAPI()
SYSTEM_ENABLED = True

@app.get("/status")
def status():
    return {"system": SYSTEM_ENABLED, "env": os.getenv("ENV", "production")}

@app.post("/kill")
def kill():
    global SYSTEM_ENABLED
    SYSTEM_ENABLED = False
    return {"status": "stopped"}

@app.post("/start")
def start():
    global SYSTEM_ENABLED
    SYSTEM_ENABLED = True
    return {"status": "running"}
PYCODE

cat > "$APP_DIR/agent/requirements.txt" <<'REQ'
requests==2.32.3
REQ

cat > "$APP_DIR/agent/Dockerfile" <<'DOCKER'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python","agent.py"]
DOCKER

cat > "$APP_DIR/agent/agent.py" <<'PYCODE'
import os
import time

import requests

CONTROL_URL = os.getenv("CONTROL_URL", "http://control:8080")
MAX_SPEND = int(os.getenv("MAX_DAILY_SPEND", "100"))

def check_budget(amount: int) -> None:
    if amount > MAX_SPEND:
        raise RuntimeError("budget_exceeded")

def system_enabled() -> bool:
    try:
        response = requests.get(f"{CONTROL_URL}/status", timeout=2)
        response.raise_for_status()
        return bool(response.json().get("system"))
    except Exception:
        return False

def run() -> None:
    while True:
        if not system_enabled():
            time.sleep(5)
            continue
        try:
            check_budget(0)
            print("Agent running business logic...")
        except RuntimeError as exc:
            print(f"Agent halted: {exc}")
            time.sleep(10)
            continue
        time.sleep(3)

if __name__ == "__main__":
    run()
PYCODE

cat > "$APP_DIR/prometheus/prometheus.yml" <<'PROM'
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: "api"
    static_configs:
      - targets: ["api:8000"]
  - job_name: "control"
    static_configs:
      - targets: ["control:8080"]
PROM

cat > "$APP_DIR/db/init.sql" <<SQL
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE TABLE IF NOT EXISTS users(
  id SERIAL PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  tenant_id UUID,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
INSERT INTO users(username,password,role)
VALUES('admin', crypt('${ADMIN_PASS}', gen_salt('bf', 12)), 'admin')
ON CONFLICT (username) DO NOTHING;
SQL

cat > "$APP_DIR/api/requirements.txt" <<'REQ'
fastapi==0.110.0
uvicorn==0.29.0
REQ

cat > "$APP_DIR/api/Dockerfile" <<'DOCKER'
FROM python:3.11-slim
RUN useradd -m -u 10001 appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
USER appuser
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]
DOCKER

cat > "$APP_DIR/api/main.py" <<'PYCODE'
from fastapi import FastAPI
app = FastAPI(title="zTTato SaaS API")
@app.get('/health')
def health():
    return {'ok': True}
PYCODE

cat > "$APP_DIR/worker/requirements.txt" <<'REQ'
REQ
cat > "$APP_DIR/worker/Dockerfile" <<'DOCKER'
FROM python:3.11-slim
WORKDIR /app
COPY . .
CMD ["python","worker.py"]
DOCKER
cat > "$APP_DIR/worker/worker.py" <<'PYCODE'
import time
while True:
    print('worker tick')
    time.sleep(5)
PYCODE

cat > "$APP_DIR/analytics/requirements.txt" <<'REQ'
REQ
cat > "$APP_DIR/analytics/Dockerfile" <<'DOCKER'
FROM python:3.11-slim
WORKDIR /app
COPY . .
CMD ["python","analytics_worker.py"]
DOCKER
cat > "$APP_DIR/analytics/analytics_worker.py" <<'PYCODE'
import time
while True:
    print('analytics tick')
    time.sleep(5)
PYCODE

cat > "$APP_DIR/panels/admin/index.html" <<'HTML'
<!doctype html><html><body><h1>Admin Panel</h1></body></html>
HTML
cat > "$APP_DIR/panels/user/index.html" <<'HTML'
<!doctype html><html><body><h1>User Panel</h1></body></html>
HTML
cat > "$APP_DIR/panels/devops/index.html" <<'HTML'
<!doctype html><html><body><h1>DevOps Panel</h1></body></html>
HTML

cat > "$APP_DIR/infra/nginx.conf" <<'NGINX'
events {}
http {
  server { listen 80; return 301 https://$host$request_uri; }
  server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/certs/tls.crt;
    ssl_certificate_key /etc/nginx/certs/tls.key;
    location /api/ { proxy_pass http://api:8000; }
    location /admin/ { alias /usr/share/nginx/html/admin/; }
    location /user/ { alias /usr/share/nginx/html/user/; }
    location /devops/ { alias /usr/share/nginx/html/devops/; }
  }
}
NGINX

cat > "$APP_DIR/infra/nginx.Dockerfile" <<'DOCKER'
FROM nginx:alpine
COPY infra/nginx.conf /etc/nginx/nginx.conf
COPY certs /etc/nginx/certs
COPY panels/admin /usr/share/nginx/html/admin
COPY panels/user /usr/share/nginx/html/user
COPY panels/devops /usr/share/nginx/html/devops
DOCKER

cat > "$APP_DIR/infra/docker-compose.yml" <<'COMPOSE'
services:
  api:
    build: ../api
    env_file: ../api/api.env
    restart: always
    networks: [internal]
  worker:
    build: ../worker
    env_file: ../worker/worker.env
    restart: always
    networks: [internal]
  analytics_worker:
    build: ../analytics
    env_file: ../worker/worker.env
    restart: always
    networks: [internal]
  control:
    build: ../control
    restart: always
    ports: ["8080:8080"]
    networks: [internal]
  agent:
    build: ../agent
    restart: always
    environment:
      CONTROL_URL: http://control:8080
      MAX_DAILY_SPEND: ${MAX_DAILY_SPEND}
      ENABLE_AGENTS: ${ENABLE_AGENTS}
    depends_on: [control]
    networks: [internal]
  db:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_DB: zttato
      POSTGRES_USER: zttato
      POSTGRES_PASSWORD: ${DB_PASS}
    volumes:
      - db_data:/var/lib/postgresql/data
      - ../db/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks: [internal]
  redis:
    image: redis:7
    restart: always
    command: ["redis-server","--requirepass","${REDIS_PASS}"]
    networks: [internal]
  nginx:
    build:
      context: ..
      dockerfile: infra/nginx.Dockerfile
    restart: always
    ports: ["80:80","443:443"]
    depends_on: [api]
    networks: [internal, public]
volumes:
  db_data:
networks:
  internal:
    internal: true
  public:
COMPOSE

if [[ "$BUILD_FULL_PACK" == "true" ]]; then
cat > "$APP_DIR/k8s/namespace.yaml" <<'YAML'
apiVersion: v1
kind: Namespace
metadata:
  name: zttato
YAML
cat > "$APP_DIR/k8s/deploy.sh" <<'BASH'
#!/usr/bin/env bash
set -euo pipefail
kubectl apply -f namespace.yaml
BASH
chmod +x "$APP_DIR/k8s/deploy.sh"
fi

cat > "$APP_DIR/backup/backup.sh" <<'BASH'
#!/usr/bin/env bash
set -euo pipefail
TS=$(date +%F_%H-%M)
FILE="/opt/zttato-platform/backup/db_${TS}.sql.gz"
ENCRYPTED_FILE="${FILE}.enc"
BACKUP_KEY_FILE="/opt/zttato-platform/backup/.backup_key"
DB_CONTAINER=$(docker compose -f /opt/zttato-platform/infra/docker-compose.yml ps -q db)
docker exec "$DB_CONTAINER" pg_dump -U zttato zttato | gzip > "$FILE"
test -s "$FILE"
if [[ ! -f "$BACKUP_KEY_FILE" ]]; then
  umask 077
  openssl rand -hex 32 > "$BACKUP_KEY_FILE"
fi
openssl enc -aes-256-cbc -pbkdf2 -salt -in "$FILE" -out "$ENCRYPTED_FILE" -pass "file:${BACKUP_KEY_FILE}"
rm -f "$FILE"
find /opt/zttato-platform/backup -type f -mtime +7 -delete
BASH
chmod +x "$APP_DIR/backup/backup.sh"

cat > "$APP_DIR/monitor/health.sh" <<'BASH'
#!/usr/bin/env bash
set -euo pipefail
curl -fs http://localhost/ >/dev/null || echo "ALERT: nginx down"
curl -kfs https://localhost/ >/dev/null || echo "ALERT: nginx down (https)"
BASH
chmod +x "$APP_DIR/monitor/health.sh"

log "[4/8] Start stack"
cd "$APP_DIR/infra"
cp "$APP_DIR/.env" "$APP_DIR/infra/.env"
docker compose up -d --build

log "[5/8] Setup firewall and cron"
ufw --force default deny incoming
ufw --force default allow outgoing
ufw --force limit 22/tcp
ufw --force limit 80/tcp
ufw --force limit 443/tcp
ufw --force enable

(crontab -l 2>/dev/null; echo "0 */6 * * * ${APP_DIR}/backup/backup.sh") | crontab -
(crontab -l 2>/dev/null; echo "*/5 * * * * ${APP_DIR}/monitor/health.sh") | crontab -

cat > /etc/systemd/system/zttato.service <<EOF
[Unit]
Description=zTTato Stack
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=true
WorkingDirectory=${APP_DIR}/infra
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable zttato

if [[ -n "$CERT_EMAIL" && "$DOMAIN" != "localhost" && "$DOMAIN" != *.local ]]; then
  (crontab -l 2>/dev/null; echo "0 2 * * * certbot renew --quiet && docker compose -f ${APP_DIR}/infra/docker-compose.yml restart nginx") | crontab -
fi

if [[ "$EXPORT_ZIP" == "true" ]]; then
  log "[7/8] Export project archive"
  (cd /opt && zip -rq zttato-platform.zip zttato-platform)
fi

log "[8/8] Completed"
cat <<MSG
Installed at: ${APP_DIR}
URL: https://${DOMAIN}
Panels:
  - https://${DOMAIN}/admin/
  - https://${DOMAIN}/user/
  - https://${DOMAIN}/devops/
API:
  - GET /api/health
Control plane:
  - GET http://localhost:8080/status
  - POST http://localhost:8080/kill
  - POST http://localhost:8080/start
NOTE: Set OPENAI_API_KEY in ${APP_DIR}/api/api.env before production usage.
NOTE: Bootstrap admin user is created with username 'admin' and generated password '${ADMIN_PASS}' (rotate immediately).
API-specific secrets: ${APP_DIR}/api/api.env
Worker-specific secrets: ${APP_DIR}/worker/worker.env
ZIP export: $( [[ "$EXPORT_ZIP" == "true" ]] && echo "/opt/zttato-platform.zip" || echo "disabled (use --export-zip)" )
K8s full pack: $( [[ "$BUILD_FULL_PACK" == "true" ]] && echo "${APP_DIR}/k8s (apply with ./deploy.sh)" || echo "disabled (--skip-full-pack used)" )
MSG
