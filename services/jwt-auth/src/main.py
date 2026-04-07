from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import json
import os
import re
from typing import Any, Dict, Optional

try:
    import jwt
except ModuleNotFoundError:  # pragma: no cover - dependency optional in unit tests
    class _SimpleJWT:
        class InvalidTokenError(Exception):
            pass

        class ExpiredSignatureError(InvalidTokenError):
            pass

        class InvalidAudienceError(InvalidTokenError):
            pass

        class InvalidIssuerError(InvalidTokenError):
            pass

        @staticmethod
        def _b64encode(raw: bytes) -> str:
            return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

        @staticmethod
        def _b64decode(data: str) -> bytes:
            padding = "=" * (-len(data) % 4)
            return base64.urlsafe_b64decode((data + padding).encode())

        @classmethod
        def encode(cls, payload: Dict[str, Any], secret: str, algorithm: str, headers: Optional[Dict[str, Any]] = None) -> str:
            if algorithm != "HS256":
                raise cls.InvalidTokenError("Unsupported algorithm")
            token_headers = {"typ": "JWT", "alg": algorithm, **(headers or {})}
            header_part = cls._b64encode(json.dumps(token_headers, separators=(",", ":")).encode())
            payload_part = cls._b64encode(json.dumps(payload, separators=(",", ":")).encode())
            signing_input = f"{header_part}.{payload_part}".encode()
            signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
            return f"{header_part}.{payload_part}.{cls._b64encode(signature)}"

        @classmethod
        def decode(
            cls,
            token: str,
            secret: str,
            audience: str,
            issuer: str,
            algorithms: list[str],
            options: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            if "HS256" not in algorithms:
                raise cls.InvalidTokenError("Unsupported algorithm")

            try:
                header_part, payload_part, signature_part = token.split(".")
            except ValueError as exc:
                raise cls.InvalidTokenError("Malformed token") from exc

            signing_input = f"{header_part}.{payload_part}".encode()
            expected_signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
            provided_signature = cls._b64decode(signature_part)
            if not hmac.compare_digest(expected_signature, provided_signature):
                raise cls.InvalidTokenError("Invalid signature")

            payload = json.loads(cls._b64decode(payload_part).decode())
            required = set((options or {}).get("require", []))
            missing = [claim for claim in required if claim not in payload]
            if missing:
                raise cls.InvalidTokenError(f"Missing required claims: {','.join(missing)}")

            now_ts = int(datetime.now(tz=timezone.utc).timestamp())
            if int(payload.get("exp", 0)) <= now_ts:
                raise cls.ExpiredSignatureError("Token expired")
            if payload.get("aud") != audience:
                raise cls.InvalidAudienceError("Invalid audience")
            if payload.get("iss") != issuer:
                raise cls.InvalidIssuerError("Invalid issuer")
            return payload

    jwt = _SimpleJWT()
from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI(title="jwt-auth", version="1.0.0")

JWT_ISSUER = os.getenv("JWT_ISSUER", "https://jwt-auth.platform.svc.cluster.local")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "zlttbots")
JWT_SECRET = os.getenv("JWT_SECRET")
IS_TEST_RUNTIME = "PYTEST_CURRENT_TEST" in os.environ
if not JWT_SECRET and IS_TEST_RUNTIME:
    JWT_SECRET = "unit-test-secret-do-not-use-in-production"
if not JWT_SECRET or JWT_SECRET == "change-me-in-production":
    raise RuntimeError("CRITICAL: JWT_SECRET is not set or uses insecure default.")
if len(JWT_SECRET) < 32 and not IS_TEST_RUNTIME:
    raise RuntimeError("CRITICAL: JWT_SECRET must be at least 32 characters.")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ALLOWED_ALGORITHMS = {"HS256"}
if JWT_ALGORITHM not in ALLOWED_ALGORITHMS:
    raise RuntimeError("CRITICAL: Unsupported JWT_ALGORITHM configured.")


def _parse_positive_int_env(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        parsed = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"CRITICAL: {name} must be a valid integer.") from exc
    if parsed < minimum or parsed > maximum:
        raise RuntimeError(f"CRITICAL: {name} must be between {minimum} and {maximum}.")
    return parsed


DEFAULT_TOKEN_TTL_MINUTES = _parse_positive_int_env(
    "JWT_TTL_MINUTES",
    30,
    minimum=1,
    maximum=1440,
)
MAX_SUBJECT_LENGTH = 128
MAX_SCOPE_LENGTH = 512
SUBJECT_PATTERN = re.compile(r"^[A-Za-z0-9:_\-.]+$")
SCOPE_PATTERN = re.compile(r"^[A-Za-z0-9:_\-. ]*$")


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
    normalized_subject = subject.strip()
    normalized_scopes = (scopes or "").strip()
    if not normalized_subject:
        raise HTTPException(status_code=400, detail="Subject is required")
    if len(normalized_subject) > MAX_SUBJECT_LENGTH:
        raise HTTPException(status_code=400, detail="Subject is too long")
    if not SUBJECT_PATTERN.fullmatch(normalized_subject):
        raise HTTPException(status_code=400, detail="Subject contains invalid characters")
    if len(normalized_scopes) > MAX_SCOPE_LENGTH:
        raise HTTPException(status_code=400, detail="Scopes are too long")
    if not SCOPE_PATTERN.fullmatch(normalized_scopes):
        raise HTTPException(status_code=400, detail="Scopes contain invalid characters")

    now = datetime.now(tz=timezone.utc)
    payload = {
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "sub": normalized_subject,
        "scope": normalized_scopes,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=DEFAULT_TOKEN_TTL_MINUTES)).timestamp()),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM, headers={"kid": "default"})
    return {"access_token": token, "token_type": "Bearer"}


def verify_bearer_token(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.replace("Bearer ", "", 1)
    try:
        return jwt.decode(
            token,
            JWT_SECRET,
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired") from exc
    except jwt.InvalidAudienceError as exc:
        raise HTTPException(status_code=401, detail="Invalid audience") from exc
    except jwt.InvalidIssuerError as exc:
        raise HTTPException(status_code=401, detail="Invalid issuer") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


@app.get("/introspect")
def introspect(payload: Dict[str, Any] = Depends(verify_bearer_token)) -> Dict[str, Any]:
    return {"active": True, "claims": payload}
