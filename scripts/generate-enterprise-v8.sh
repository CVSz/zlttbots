#!/usr/bin/env bash
set -e

ROOT=$(pwd)

echo "===================================="
echo "zlttbots Enterprise v8 Generator"
echo "===================================="

mkdir -p services/ai-orchestrator/src
mkdir -p services/product-discovery/src
mkdir -p services/campaign-optimizer/src

############################################
# AI ORCHESTRATOR
############################################

cat > services/ai-orchestrator/src/main.py << 'EOF'
from fastapi import FastAPI
import requests
import os
import redis

app = FastAPI()

REDIS = redis.Redis(host=os.getenv("REDIS_HOST","redis"),port=6379)

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/run-growth-cycle")
def run_growth_cycle():

    # 1 discover products
    r = requests.get("http://market-crawler:8000/crawl")

    # 2 predict viral score
    v = requests.post("http://viral-predictor:8000/predict")

    # 3 generate video
    g = requests.post("http://ai-video-generator:3000/render")

    # 4 publish
    p = requests.post("http://tiktok-uploader:3000/upload")

    REDIS.set("last_cycle","done")

    return {"status":"cycle-complete"}
EOF


cat > services/ai-orchestrator/Dockerfile << 'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY src /app
RUN pip install fastapi uvicorn redis requests
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]
EOF


############################################
# PRODUCT DISCOVERY ENGINE
############################################

cat > services/product-discovery/src/main.py << 'EOF'
from fastapi import FastAPI
import requests
import random

app = FastAPI()

@app.get("/discover")
def discover():

    products = requests.get("http://market-crawler:8000/products").json()

    scored = []

    for p in products:
        p["score"] = random.random()
        scored.append(p)

    scored.sort(key=lambda x:x["score"],reverse=True)

    return scored[:10]
EOF

cat > services/product-discovery/Dockerfile << 'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY src /app
RUN pip install fastapi uvicorn requests
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]
EOF


############################################
# CAMPAIGN OPTIMIZER
############################################

cat > services/campaign-optimizer/src/main.py << 'EOF'
from fastapi import FastAPI
import psycopg2
import os

app = FastAPI()

def db():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST","postgres"),
        user="zlttbots",
        password="zlttbots",
        dbname="zlttbots"
    )

@app.post("/optimize")
def optimize():

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT campaign_id, SUM(clicks) as c FROM clicks GROUP BY campaign_id")

    rows = cur.fetchall()

    best = max(rows,key=lambda x:x[1]) if rows else None

    return {"best_campaign":best}
EOF


cat > services/campaign-optimizer/Dockerfile << 'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY src /app
RUN pip install fastapi uvicorn psycopg2-binary
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]
EOF


############################################
# UPDATE DOCKER COMPOSE
############################################

if ! grep -q ai-orchestrator docker-compose.enterprise.yml; then

cat >> docker-compose.enterprise.yml << 'EOF'

  ai-orchestrator:
    build: ./services/ai-orchestrator
    container_name: zlttbots-ai-orchestrator
    depends_on:
      - market-crawler
      - viral-predictor
      - redis
    networks:
      - zlttbots-net

  product-discovery:
    build: ./services/product-discovery
    container_name: zlttbots-product-discovery
    networks:
      - zlttbots-net

  campaign-optimizer:
    build: ./services/campaign-optimizer
    container_name: zlttbots-campaign-optimizer
    networks:
      - zlttbots-net
EOF

fi


############################################
# GIT PUSH
############################################

git add .
git commit -m "upgrade: zlttbots Enterprise v8 autonomous AI growth engine"

git push git@github.com:ZeaZDev/zlttbots.git


echo "===================================="
echo "Enterprise v8 Generated"
echo "===================================="
