import hashlib
import hmac
import os

from fastapi import HTTPException, Request, Security
from fastapi.security.api_key import APIKeyHeader

_API_KEY = os.getenv("API_KEY")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

_WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")


def require_api_key(key: str = Security(_api_key_header)) -> None:
    """
    Checks X-API-Key header against the API_KEY env var.
    Auth is disabled when API_KEY is not set (local dev).
    """
    if _API_KEY is None:
        return
    if key is None or not hmac.compare_digest(key, _API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


async def require_webhook_signature(request: Request) -> None:
    """
    Verifies the X-Webhook-Signature header against an HMAC-SHA256 digest
    of the raw request body, keyed by the WEBHOOK_SECRET env var — same
    constant-time-comparison idiom as require_api_key, applied to a
    computed digest instead of a shared string. Signature check is a no-op
    when WEBHOOK_SECRET is unset (local dev), same as API_KEY.

    Reads the raw body via request.body() before the route handler parses
    it as JSON — Starlette caches the body after the first read, so the
    route's Pydantic body model still parses correctly afterward.
    """
    if _WEBHOOK_SECRET is None:
        return

    signature = request.headers.get("X-Webhook-Signature")
    body = await request.body()
    expected = hmac.new(_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()

    if signature is None or not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing webhook signature")
