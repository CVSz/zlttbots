import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient

MODULE_PATH = Path("services/security-api/src/main.py")
SPEC = importlib.util.spec_from_file_location("security_api_main", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_healthz() -> None:
    client = TestClient(MODULE.app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_validate_repo_url_rejects_http() -> None:
    try:
        MODULE._validate_repo_url("http://github.com/org/repo")
    except Exception as exc:  # noqa: BLE001
        assert "Only HTTPS" in str(exc)
    else:
        raise AssertionError("Expected URL validation to fail")
