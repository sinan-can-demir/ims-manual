# tests/test_security_headers.py

from fastapi.testclient import TestClient

from app.main import app


def test_security_headers_present_on_plain_http():
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_hsts_absent_over_plain_http():
    """Local dev and the no-domain plain-HTTP prod path have no
    X-Forwarded-Proto header — HSTS must not be asserted there, or
    browsers would force HTTPS on a host that doesn't serve it."""
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/health")

    assert "strict-transport-security" not in response.headers


def test_hsts_present_when_forwarded_as_https():
    """Caddy/ALB terminate TLS upstream and forward X-Forwarded-Proto —
    uvicorn itself always sees plain HTTP, so this is the only signal
    available that the original request was HTTPS."""
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/health", headers={"X-Forwarded-Proto": "https"})

    assert response.headers["strict-transport-security"] == "max-age=63072000; includeSubDomains"
