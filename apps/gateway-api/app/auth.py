"""Azure AD JWT validation and RBAC middleware."""
from __future__ import annotations
import httpx
from functools import lru_cache
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt, JWTError
import structlog

from app.config import settings

log = structlog.get_logger()

# When AZURE_CLIENT_ID is not set we are in dev/demo mode — auth is bypassed
DEV_MODE = not settings.azure_client_id

DEMO_USER = {
    "sub": "demo-user-001",
    "preferred_username": "demo.apc@upv.local",
    "roles": ["APC"],
    "oid": "demo-user-001",
}

bearer_scheme = HTTPBearer(auto_error=False)   # auto_error=False so we can handle missing tokens ourselves

ROLES = {"APC", "ADMIN", "VIEWER"}


@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    if not settings.azure_jwks_url:
        return {"keys": []}
    with httpx.Client() as client:
        resp = client.get(settings.azure_jwks_url)
        resp.raise_for_status()
        return resp.json()


def decode_token(token: str) -> dict:
    try:
        jwks = _get_jwks()
        if not jwks.get("keys"):
            # Dev mode — accept any token including "demo-token"
            try:
                return jwt.decode(token, key="", options={"verify_signature": False})
            except Exception:
                return DEMO_USER
        from jose.backends import RSAKey
        header = jwt.get_unverified_header(token)
        key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
        if not key:
            raise HTTPException(status_code=401, detail="Public key not found")
        return jwt.decode(token, key, algorithms=["RS256"], audience=settings.azure_client_id)
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")


class CurrentUser:
    def __init__(self, user_id: str, email: str, role: str, azure_oid: str):
        self.user_id = user_id
        self.email = email
        self.role = role
        self.azure_oid = azure_oid


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    # Dev mode with no token — return demo APC user
    if DEV_MODE and credentials is None:
        payload = DEMO_USER
    elif credentials is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated")
    else:
        payload = decode_token(credentials.credentials)

    return CurrentUser(
        user_id=payload.get("sub", "demo-user-001"),
        email=payload.get("preferred_username", payload.get("email", "demo@upv.local")),
        role=(payload.get("roles") or ["APC"])[0],
        azure_oid=payload.get("oid", payload.get("sub", "demo-user-001")),
    )


def require_role(*roles: str):
    async def checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Role {current_user.role} not authorized")
        return current_user
    return checker


require_apc = require_role("APC", "ADMIN")
require_admin = require_role("ADMIN")
