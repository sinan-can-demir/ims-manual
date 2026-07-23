# app/core/rate_limit.py

import os

from slowapi import Limiter
from starlette.requests import Request

_DEFAULT_RATE_LIMIT = os.getenv("RATE_LIMIT", "100/minute")


def rate_limit_key(request: Request) -> str:
    """
    Always keys by client IP, never by the presented X-API-Key value.
    IMS has exactly one valid shared key (no per-user keys), so keying by
    the presented value would let an attacker reset their bucket on every
    request just by guessing a different key each time — defeating the
    brute-force mitigation this is meant to provide.
    """
    return request.client.host if request.client else "unknown"


# Storage defaults to slowapi's in-process memory:// backend, which is not
# shared across Gunicorn's worker processes in prod (WEB_CONCURRENCY,
# docker-compose.prod.yml) — same class of gap PROMETHEUS_MULTIPROC_DIR
# exists to solve for /metrics, unaddressed here. Effective limit in prod
# is therefore ~WEB_CONCURRENCY x RATE_LIMIT, not exactly RATE_LIMIT. See
# SECURITY.md.
limiter = Limiter(key_func=rate_limit_key, default_limits=[_DEFAULT_RATE_LIMIT])
