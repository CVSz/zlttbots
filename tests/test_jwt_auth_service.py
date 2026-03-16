from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient


def _load_jwt_auth_app():
    module_path = Path(__file__).resolve().parents[1] / 'services' / 'jwt-auth' / 'src' / 'main.py'
    spec = spec_from_file_location('jwt_auth_main', module_path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app


def test_token_and_introspect_round_trip() -> None:
    app = _load_jwt_auth_app()
    client = TestClient(app)

    response = client.post('/token', params={'subject': 'svc-analytics', 'scopes': 'read:events'})
    assert response.status_code == 200
    token = response.json()['access_token']

    introspect = client.get('/introspect', headers={'Authorization': f'Bearer {token}'})
    assert introspect.status_code == 200
    claims = introspect.json()['claims']
    assert claims['sub'] == 'svc-analytics'
    assert claims['scope'] == 'read:events'
