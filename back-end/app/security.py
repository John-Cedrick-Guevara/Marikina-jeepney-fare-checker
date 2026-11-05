import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from threading import Lock
from typing import Annotated

import jwt
from fastapi import Header, HTTPException, Request

logger = logging.getLogger(__name__)


@lru_cache
def _jwks_client() -> jwt.PyJWKClient:
    """Supabase Auth's public signing keys, fetched once and cached."""
    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    return jwt.PyJWKClient(f"{supabase_url}/auth/v1/.well-known/jwks.json", cache_keys=True)


def signing_key(token: str):
    """The public key that signed a Supabase access token."""
    return _jwks_client().get_signing_key_from_jwt(token).key


@dataclass
class Admin:
    user_id: str
    email: str


def require_admin(authorization: Annotated[str | None, Header()] = None) -> Admin:
    """
    Allow the request only for a signed-in Supabase user whose app_metadata.role is "admin".
    app_metadata can only be set server-side (SQL or the Supabase dashboard), not by the user.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Please sign in as an admin.")
    token = authorization[7:]

    try:
        claims = jwt.decode(token, signing_key(token), algorithms=["ES256", "RS256"], audience="authenticated")
    except (jwt.PyJWTError, jwt.PyJWKClientError) as err:
        logger.info("Rejected admin token: %s", err)
        raise HTTPException(status_code=401, detail="Your session has expired. Please sign in again.")

    if (claims.get("app_metadata") or {}).get("role") != "admin":
        raise HTTPException(status_code=403, detail="This account is not an admin.")

    return Admin(user_id=claims["sub"], email=claims.get("email", ""))


class RateLimiter:
    """
    Per-IP request limit over a fixed window, used as a FastAPI dependency.
    """

    # ponytail: in-process fixed window (allows up to 2x the limit across a window edge, not
    # shared between workers); move to a shared store (Redis) when running several instances
    def __init__(self, limit: int, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self._window = 0
        self._counts: dict[str, int] = defaultdict(int)
        self._lock = Lock()

    def __call__(self, request: Request) -> None:
        # Behind a reverse proxy, run uvicorn with --proxy-headers so this is the real client IP
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = int(now // self.window_seconds)

        with self._lock:
            # A new window starts every client from zero, which also keeps memory bounded
            if window != self._window:
                self._window = window
                self._counts.clear()
            self._counts[client_ip] += 1
            over_limit = self._counts[client_ip] > self.limit

        if over_limit:
            retry_after = int((window + 1) * self.window_seconds - now) + 1
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please wait a moment and try again.",
                headers={"Retry-After": str(retry_after)},
            )


# General limit for the public endpoints
public_rate_limit = RateLimiter(limit=int(os.getenv("PUBLIC_RATE_LIMIT_PER_MINUTE", "60")))
