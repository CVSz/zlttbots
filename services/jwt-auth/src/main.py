from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI(title="jwt-auth", version="1.0.0")

JWT_ISSUER = os.getenv("JWT_ISSUER", "https://jwt-auth.platform.svc.cluster.local")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "zttato-platform")
JWT_SECRET = os.getenv("JWT_SECRET")
IS_TEST_RUNTIME = "PYTEST_CURRENT_TEST" in os.environ
if not JWT_SECRET and IS_TEST_RUNTIME:
    JWT_SECRET = "unit-test-secret-do-not-use-in-production"
if not JWT_SECRET or JWT_SECRET == "change-me-in-production":
    raise RuntimeError("CRITICAL: JWT_SECRET is not set or uses insecure default.")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
DEFAULT_TOKEN_TTL_MINUTES = int(os.getenv("JWT_TTL_MINUTES", "30"))


def _b64url_encode(payload: bytes) -> str:
    return urlsafe_b64encode(payload).rstrip(b"=").decode("utf-8")


def _b64url_decode(payload: str) -> bytes:
    padding = "=" * ((4 - len(payload) % 4) % 4)
    return urlsafe_b64decode((payload + padding).encode("utf-8"))


def _encode_token(claims: Dict[str, Any]) -> str:
    header = {"alg": JWT_ALGORITHM, "typ": "JWT", "kid": "default"}
    signing_input = f"{_b64url_encode(json.dumps(header, separators=(',', ':')).encode())}.{_b64url_encode(json.dumps(claims, separators=(',', ':')).encode())}"
    signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def _decode_token(token: str) -> Dict[str, Any]:
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid token format") from exc

    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    expected_signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()

    provided_signature = _b64url_decode(encoded_signature)
    if not hmac.compare_digest(expected_signature, provided_signature):
        raise HTTPException(status_code=401, detail="Invalid token signature")

    claims = json.loads(_b64url_decode(encoded_payload))
    now = int(datetime.now(tz=timezone.utc).timestamp())

    if claims.get("iss") != JWT_ISSUER:
        raise HTTPException(status_code=401, detail="Invalid issuer")
    if claims.get("aud") != JWT_AUDIENCE:
        raise HTTPException(status_code=401, detail="Invalid audience")
    if int(claims.get("exp", 0)) < now:
        raise HTTPException(status_code=401, detail="Token expired")

    return claims


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/.well-known/jwks.json")
def jwks() -> Dict[str, Any]:
    return {
        "keys": [
            {
                "kty": "oct",
                "alg": JWT_ALGORITHM,
                "k": "***",
                "kid": "default",
            }
        ]
    }


@app.post("/token")
def issue_token(subject: str, scopes: Optional[str] = "") -> Dict[str, str]:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "sub": subject,
        "scope": scopes,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=DEFAULT_TOKEN_TTL_MINUTES)).timestamp()),
    }
    token = _encode_token(payload)
    return {"access_token": token, "token_type": "Bearer"}


def verify_bearer_token(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.replace("Bearer ", "", 1)
    return _decode_token(token)


@app.get("/introspect")
def introspect(payload: Dict[str, Any] = Depends(verify_bearer_token)) -> Dict[str, Any]:
    return {"active": True, "claims": payload}
