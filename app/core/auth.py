import hmac
import os

from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

_API_KEY = os.getenv("API_KEY")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str = Security(_api_key_header)) -> None:
    """
    Checks X-API-Key header against the API_KEY env var.
    Auth is disabled when API_KEY is not set (local dev).
    """
    if _API_KEY is None:
        return
    if key is None or not hmac.compare_digest(key, _API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
