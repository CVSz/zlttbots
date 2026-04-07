from pathlib import Path


def test_frontend_does_not_ship_seeded_credentials():
    app_source = Path("apps/frontend/src/App.tsx").read_text(encoding="utf-8")
    assert 'useState("founder@zlttbots.dev")' not in app_source
    assert 'useState("ChangeMe123456")' not in app_source


def test_frontend_requires_credentials_before_auth_calls():
    app_source = Path("apps/frontend/src/App.tsx").read_text(encoding="utf-8")
    assert "Registration requires both email and password." in app_source
    assert "Login requires both email and password." in app_source
