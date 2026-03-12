#!/usr/bin/env bash
set -e

SERVICES=(
market-crawler
arbitrage-engine
gpu-renderer
viral-predictor
)

for SVC in "${SERVICES[@]}"
do

DIR="services/$SVC"

mkdir -p "$DIR"

cat > "$DIR/Dockerfile" <<EOF
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt || true

COPY src ./src

CMD ["python","src/main.py"]
EOF

echo "Dockerfile created: $SVC"

done
