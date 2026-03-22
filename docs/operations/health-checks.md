# Health Checks

เอกสารนี้รวบรวม health endpoints มาตรฐานของบริการหลักใน stack และวิธีตรวจสอบแบบเร็ว

## Service health endpoints

| Service | Container Port | Endpoint | Dependency check |
|---|---:|---|---|
| viral-predictor | 9100 | `/healthz` | PostgreSQL (`select 1`) |
| market-crawler | 9400 | `/healthz` | Redis (`PING`) |
| arbitrage-engine | 9500 | `/healthz` | PostgreSQL (`select 1`) |
| gpu-renderer | 9300 | `/healthz` | Redis (`PING`) |
| nginx (edge proxy) | 80 | `/` | Proxy process alive |
| product-discovery | 8000 | `/healthz` | market-crawler reachability with retry/timeout |

## Quick checks

เมื่อ stack รันด้วย `docker compose up -d`:

```bash
docker compose ps
```

ตรวจ endpoint ผ่านเครือข่ายภายใน compose:

```bash
docker compose exec -T nginx wget -qO- http://viral-predictor:9100/healthz
docker compose exec -T nginx wget -qO- http://market-crawler:9400/healthz
docker compose exec -T nginx wget -qO- http://arbitrage-engine:9500/healthz
docker compose exec -T nginx wget -qO- http://gpu-renderer:9300/healthz
```

## Integration smoke test

ใช้สคริปต์กลาง:

```bash
./scripts/test-integration.sh
```

สคริปต์นี้จะ:

1. รัน `docker compose up -d` (เฉพาะบริการหลัก)
2. ตรวจว่า services สำคัญอยู่ในสถานะ `running`
3. ยิง smoke tests ที่ endpoint proxy (`/`, `/predict`, `/crawl`, `/arbitrage`)


## Enterprise stack note

สำหรับ `docker-compose.enterprise.yml` ตอนนี้ `product-discovery` มี health endpoint และ Compose healthcheck แล้ว ดังนั้นสามารถใช้ `docker compose -f docker-compose.enterprise.yml ps` เพื่อตรวจสถานะได้โดยตรง.
