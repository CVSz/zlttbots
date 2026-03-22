from __future__ import annotations

import logging
import os
from typing import Iterable

import requests

log = logging.getLogger(__name__)
DEFAULT_TIMEOUT = float(os.getenv("REGION_SYNC_TIMEOUT", "1.5"))
REGIONS = [
    region.strip()
    for region in os.getenv("REGION_SYNC_ENDPOINTS", "http://asia,http://us,http://eu").split(",")
    if region.strip()
]


def broadcast(data: dict, regions: Iterable[str] | None = None) -> None:
    for region in regions or REGIONS:
        try:
            response = requests.post(f"{region}/sync", json=data, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as exc:
            log.warning("region sync failed for %s: %s", region, exc)
