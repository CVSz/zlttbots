from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=REPO_ROOT, check=False, capture_output=True, text=True)


def test_feature_impact_dive_help_smoke() -> None:
    result = run_command(sys.executable, "scripts/feature_impact_dive.py", "--help")
    assert result.returncode == 0, result.stderr


def test_docs_snippet_validator_smoke() -> None:
    result = run_command(sys.executable, "scripts/validate_docs_snippets.py")
    assert result.returncode == 0, result.stdout + result.stderr


def test_node_dependency_scan_shell_syntax() -> None:
    result = run_command("bash", "-n", "infrastructure/scripts/node-dependency-scan.sh")
    assert result.returncode == 0, result.stderr
