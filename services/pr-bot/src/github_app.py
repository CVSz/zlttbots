from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import jwt
import requests

from .config import GitHubAppConfig


@dataclass(frozen=True)
class InstallationToken:
    token: str
    expires_at: str


class GitHubAppAuthError(RuntimeError):
    """Raised when GitHub App auth fails."""


class GitHubAppAuth:
    def __init__(self, config: GitHubAppConfig, api_base_url: str = "https://api.github.com") -> None:
        self._config = config
        self._api_base_url = api_base_url.rstrip("/")

    def generate_jwt(self) -> str:
        now = int(time.time())
        payload = {"iat": now - 60, "exp": now + 600, "iss": self._config.app_id}
        return jwt.encode(payload, self._config.private_key_pem, algorithm="RS256")

    def get_installation_token(self, installation_id: int) -> InstallationToken:
        jwt_token = self.generate_jwt()
        response = requests.post(
            f"{self._api_base_url}/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=15,
        )
        if response.status_code >= 400:
            raise GitHubAppAuthError(
                f"GitHub installation token exchange failed ({response.status_code}): {response.text[:200]}"
            )
        payload: dict[str, Any] = response.json()
        token = str(payload.get("token", "")).strip()
        expires_at = str(payload.get("expires_at", "")).strip()
        if not token or not expires_at:
            raise GitHubAppAuthError("GitHub installation response missing token or expires_at")
        return InstallationToken(token=token, expires_at=expires_at)
