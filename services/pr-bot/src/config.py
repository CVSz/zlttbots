from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """Raised when required runtime configuration is missing or invalid."""



def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(f"{name} is required")
    return value


@dataclass(frozen=True)
class GitHubAppConfig:
    app_id: str
    private_key_pem: str
    webhook_secret: str

    @classmethod
    def from_env(cls) -> "GitHubAppConfig":
        return cls(
            app_id=_require_env("GH_APP_ID"),
            private_key_pem=_require_env("GH_PRIVATE_KEY").replace("\\n", "\n"),
            webhook_secret=_require_env("GH_WEBHOOK_SECRET"),
        )
