"""Azure AD JWT validation and RBAC middleware."""
from __future__ import annotations
import httpx
from functools import lru_cache
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import structlog

from app.config import settings

log = structlog.get_logger()

bearer_scheme = HTTPBearer()

ROLES = {"APC", "ADMIN", "VIEWER"}


@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    """Fetch Azure AD JWKS (cached)."""
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
            # Dev mode: decode without verification
            return jwt.decode(token, key="", options={"verify_signature": False})

        from jose.backends import RSAKey
        header = jwt.get_unverified_header(token)
        key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
        if not key:
            raise HTTPException(status_code=401, detail="Public key not found")

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.azure_client_id,
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")


class CurrentUser:
    def __init__(self, user_id: str, email: str, role: str, azure_oid: str):
        self.user_id = user_id
        self.email = email
        self.role = role
        self.azure_oid = azure_oid


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> CurrentUser:
    payload = decode_token(credentials.credentials)
    return CurrentUser(
        user_id=payload.get("sub", ""),
        email=payload.get("preferred_username", payload.get("email", "")),
        role=payload.get("roles", ["APC"])[0] if payload.get("roles") else "APC",
        azure_oid=payload.get("oid", payload.get("sub", "")),
    )


def require_role(*roles: str):
    async def checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Role {current_user.role} not authorized")
        return current_user
    return checker


require_apc = require_role("APC", "ADMIN")
require_admin = require_role("ADMIN")
