from __future__ import annotations

import os
import re

from .autofix import create_auto_fix_pr
from .server import app


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def create_pr(repo_name: str, branch: str, patch: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo_name):
        raise ValueError("repo_name must match owner/repo")
    if not re.fullmatch(r"[A-Za-z0-9_./-]+", branch):
        raise ValueError("branch has invalid characters")
    if not patch.strip():
        raise ValueError("patch content cannot be empty")

    token = _require_env("GITHUB_TOKEN")
    auto_fix = create_auto_fix_pr(token=token, repo_name=repo_name, base_branch=branch, patch=patch)
    return auto_fix.url


__all__ = ["app", "create_pr"]
