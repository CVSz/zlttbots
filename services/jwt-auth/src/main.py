from datetime import datetime, timedelta, timezone
import os
from typing import Any, Dict, Optional

import jwt
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
ALLOWED_ALGORITHMS = {"HS256"}
if JWT_ALGORITHM not in ALLOWED_ALGORITHMS:
    raise RuntimeError("CRITICAL: Unsupported JWT_ALGORITHM configured.")
DEFAULT_TOKEN_TTL_MINUTES = int(os.getenv("JWT_TTL_MINUTES", "30"))


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
