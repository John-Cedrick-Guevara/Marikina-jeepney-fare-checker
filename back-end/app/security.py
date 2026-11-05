import os
import secrets
import time
from collections import defaultdict
from threading import Lock
from typing import Annotated

from fastapi import Header, HTTPException, Request


def require_admin(x_admin_key: Annotated[str | None, Header()] = None) -> None:
    """
    Allow a write only with the admin key from ADMIN_API_KEY.
    Fails closed: with no key configured, every write is refused.
    """
    # ponytail: one shared key until the admin panel brings Supabase Auth
    expected = os.getenv("ADMIN_API_KEY")
    if not expected:
        raise HTTPException(status_code=503, detail="Admin API is not configured")
    if x_admin_key is None or not secrets.compare_digest(x_admin_key, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing admin key")


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
