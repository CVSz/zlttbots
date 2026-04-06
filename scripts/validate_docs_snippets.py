#!/usr/bin/env python3
"""Validate docs command style and referenced local paths."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"
PATH_TOKEN = re.compile(r"`((?:docs|services|scripts|infrastructure|apps)/[^`\s]+|docker-compose(?:\.enterprise)?\.yml)`")


def iter_markdown_files() -> list[Path]:
    return sorted(DOCS_ROOT.rglob("*.md"))


def validate() -> list[str]:
    errors: list[str] = []
    for doc_path in iter_markdown_files():
        rel = doc_path.relative_to(REPO_ROOT)
        content = doc_path.read_text(encoding="utf-8")

        if "docker-compose " in content:
            errors.append(f"{rel}: use 'docker compose' command style instead of 'docker-compose'")

        for match in PATH_TOKEN.finditer(content):
            token = match.group(1)
            if any(ch in token for ch in "*<>"):
                continue
            candidate = REPO_ROOT / token
            if not candidate.exists():
                errors.append(f"{rel}: referenced path does not exist: {token}")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(error)
        return 1
    print("docs snippets validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
