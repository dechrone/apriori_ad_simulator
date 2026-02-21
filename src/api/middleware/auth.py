"""
Firebase JWT auth middleware / dependency.

Usage (FastAPI dependency injection):

    from src.api.middleware.auth import get_current_user

    @router.post("/protected")
    async def protected(user: dict = Depends(get_current_user)):
        uid = user["uid"]
        ...

The client must send:  Authorization: Bearer <firebase_id_token>

E2E / dev: set APRIORI_SKIP_AUTH=1 to allow requests without Bearer token (mock user).
"""

import os
from typing import Dict, Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.firebase.client import verify_id_token

_bearer_required = HTTPBearer(auto_error=True)
_bearer_optional = HTTPBearer(auto_error=False)

MOCK_USER = {"uid": "test-user", "email": "test@apriori.local"}


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_optional),
) -> Dict[str, Any]:
    """
    FastAPI dependency: verifies the Firebase ID token from the Authorization header
    and returns the decoded token claims (uid, email, etc.).
    If APRIORI_SKIP_AUTH=1 and no Bearer token is sent, returns a mock user (e2e/dev).
    Raises HTTP 401 if token is required but missing, expired, or invalid.
    """
    if os.getenv("APRIORI_SKIP_AUTH") == "1" and credentials is None:
        return MOCK_USER
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required (Bearer token)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    try:
        decoded = verify_id_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return decoded
