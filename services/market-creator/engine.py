from __future__ import annotations

import time
import uuid

import requests

DISCOVERY_API = "http://market-crawler:8000/trending"
LAUNCH_API = "http://tiktok-uploader:3000/upload"



def discover() -> list[dict]:
    try:
        return requests.get(DISCOVERY_API, timeout=3).json()
    except requests.RequestException:
        return []



def validate(item: dict) -> bool:
    return item.get("engagement", 0) > 0.2



def launch(item: dict) -> bool:
    payload = {
        "id": str(uuid.uuid4()),
        "title": item["title"],
        "media_url": item["media_url"],
    }
    return requests.post(LAUNCH_API, json=payload, timeout=5).status_code == 200



def loop() -> dict[str, int]:
    launched = 0
    for item in discover():
        if validate(item) and launch(item):
            launched += 1
    return {"launched": launched, "ts": int(time.time())}
