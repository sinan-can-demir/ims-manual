# app/core/rate_limit.py

import os

from slowapi import Limiter
from starlette.requests import Request

_DEFAULT_RATE_LIMIT = os.getenv("RATE_LIMIT", "100/minute")


def rate_limit_key(request: Request) -> str:
    """
    Keys by X-API-Key when present so quota is per-caller rather than
    per-IP — several legitimate clients can share a NAT/VPS IP. Falls back
    to client IP for unauthenticated requests (API_KEY unset, local dev).
    """
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"key:{api_key}"
    return f"ip:{request.client.host if request.client else 'unknown'}"


limiter = Limiter(key_func=rate_limit_key, default_limits=[_DEFAULT_RATE_LIMIT])
