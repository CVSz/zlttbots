from __future__ import annotations

import os

import requests

LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://llm:8000/generate")


def generate_ad(product_name: str, audience: str) -> str:
    prompt = f"Create TikTok ad for {product_name} targeting {audience}"
    try:
        response = requests.post(LLM_ENDPOINT, json={"prompt": prompt}, timeout=5)
        response.raise_for_status()
        payload = response.json()
        return str(payload.get("text", "")).strip()
    except Exception:
        return f"🔥 {product_name} is trending! Perfect for {audience}."
