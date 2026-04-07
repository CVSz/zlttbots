from __future__ import annotations

from urllib.parse import urlparse

import requests

TIMEOUT_SECONDS = 2.0


def _is_url_allowed(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def ssrf_probe(url: str) -> bool:
    if not _is_url_allowed(url):
        raise ValueError("invalid probe url")
    try:
        response = requests.get(url, timeout=TIMEOUT_SECONDS, allow_redirects=False)
        response.raise_for_status()
    except requests.RequestException:
        return True
    return False


def path_traversal_probe(base_url: str) -> bool:
    if not _is_url_allowed(base_url):
        raise ValueError("invalid base url")
    probe_url = f"{base_url.rstrip('/')}/file?name=../../etc/passwd"
    response = requests.get(probe_url, timeout=TIMEOUT_SECONDS, allow_redirects=False)
    return "root:" not in response.text
