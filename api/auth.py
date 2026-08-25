"""Gated auth: off by default (AUTH_ENABLED), backend half of the feature.

When AUTH_ENABLED is false (the default), nothing in this module is wired
into any route -- see api/routes/chat.py and api/routes/models.py, which only
add `Depends(require_user_email)` to their path operations when
`AUTH_ENABLED` is true at import time, so the dependency is never invoked at
all in the disabled case (not invoked-and-no-op).

When AUTH_ENABLED is true, the frontend's NextAuth `session`/`jwt` callbacks
mint a short-lived JWT (signed with the same NEXTAUTH_SECRET shared via env)
containing at least `email`, and attach it as `Authorization: Bearer <token>`
on every /chat and /models request. `require_user_email` decodes that token
and returns the email; any missing/malformed/expired/bad-signature token
yields a clean 401.
"""

from __future__ import annotations

import os

import jwt
from fastapi import Header, HTTPException, status


def _parse_bool(value: str) -> bool:
    """Truthy iff "true" or "1", case-insensitively. Anything else (including
    unset, "false", "0", "", garbage) is falsy. Single convention, used for
    both AUTH_ENABLED (backend) and NEXT_PUBLIC_AUTH_ENABLED (frontend)."""
    return value.strip().lower() in ("true", "1")


AUTH_ENABLED = _parse_bool(os.environ.get("AUTH_ENABLED", "false"))

# Shared secret with the frontend's NextAuth config -- reusing NEXTAUTH_SECRET
# (see .env.example) rather than introducing a separate API_JWT_SECRET, to
# keep the env var count down. Only read/required when AUTH_ENABLED is true.
_JWT_SECRET = os.environ.get("NEXTAUTH_SECRET", "")
_JWT_ALGORITHM = "HS256"


async def require_user_email(authorization: str | None = Header(default=None)) -> str:
    """FastAPI dependency: require a valid `Authorization: Bearer <jwt>`
    header, decode it with the shared secret, and return the `email` claim.

    Only ever added to a route when AUTH_ENABLED is true (see chat.py /
    models.py) -- so this function assumes auth is actually turned on.
    Missing header, malformed/expired token, or bad signature -> clean 401.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
        )

    token = authorization[len("Bearer ") :].strip()

    try:
        payload = jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing email claim",
        )
    return email
