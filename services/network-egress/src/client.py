import time

import requests


class SafeHttpClient:
    def __init__(self, timeout: int = 10, retries: int = 3, backoff: float = 0.5):
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff

    def post(self, url, json=None, headers=None):
        for attempt in range(self.retries):
            try:
                response = requests.post(url, json=json, headers=headers, timeout=self.timeout)
                if response.status_code < 500:
                    return response
            except requests.RequestException:
                pass
            time.sleep(self.backoff * (2 ** attempt))

        raise RuntimeError("request failed after retries")
