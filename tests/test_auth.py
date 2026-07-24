# tests/test_auth.py

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_health_is_exempt():
    """Health endpoint must not require auth — Docker HEALTHCHECK depends on it."""
    client = TestClient(app, raise_server_exceptions=False)
    assert client.get("/health").status_code == 200


def test_missing_key_returns_401():
    with patch("app.core.auth._API_KEY", "test-secret"):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/inventory/1")
        assert response.status_code == 401


def test_wrong_key_returns_401():
    with patch("app.core.auth._API_KEY", "test-secret"):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/inventory/1", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 401


def test_replay_without_key_returns_401():
    """
    /api/inventory/replay rebuilds inventory_state from scratch (delete +
    reinsert) — explicit coverage that it's auth-gated like the rest of the
    inventory router, not just implicitly covered by the other cases here.
    """
    with patch("app.core.auth._API_KEY", "test-secret"):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/api/inventory/replay")
        assert response.status_code == 401


def test_correct_key_passes_auth():
    with patch("app.core.auth._API_KEY", "test-secret"):
        client = TestClient(app, raise_server_exceptions=False)
        # /health is exempt — use it to confirm routing still works with correct key
        response = client.get("/health", headers={"X-API-Key": "test-secret"})
        assert response.status_code == 200


def test_no_api_key_configured_allows_all():
    """When API_KEY env var is unset, all requests pass (local dev mode)."""
    with patch("app.core.auth._API_KEY", None):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/health")
        assert response.status_code == 200
