# Security Policy

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead, use [GitHub's private security advisory feature](../../security/advisories/new)
for this repository, or contact the maintainer directly through their GitHub
profile. You should get an acknowledgement within a few days — this is a
solo-maintained project, so response times aren't guaranteed to be fast, but
reports are taken seriously.

## Known limitations of the current auth model

IMS uses a single shared API key (`X-API-Key` header, checked in
`app/core/auth.py`) rather than per-user credentials, OAuth, or JWTs. This is a
deliberate, minimal design for the project's current stage, **not** a
production-grade auth system. Specifically:

- **One key for every client.** There's no per-user identity, no scoping, and
  no way to revoke a single caller's access without rotating the key for
  everyone.
- **Auth is a no-op if `API_KEY` is unset.** This is intentional for local
  development (`.env.example` documents it), but it means **you must set
  `API_KEY` before exposing this app on any network you don't fully trust**.
  A startup log line (`AUTH DISABLED — API_KEY not set`) warns loudly if the
  app boots without it, precisely so this isn't easy to miss in a deployed
  environment's logs.
- **The comparison is constant-time** (`hmac.compare_digest`), so the auth
  check itself isn't vulnerable to a timing attack — but that only protects
  the comparison, not the broader single-shared-secret design above.

If you need per-user auth, OAuth, or anything beyond "one shared secret keeps
casual/opportunistic access out," this project isn't there yet — see
[`ROADMAP.md`](ROADMAP.md) (Epoch 7) for what's planned.

## Webhook signature verification

`POST /api/webhooks/ingest` (see [`ROADMAP.md`](ROADMAP.md) Epoch 7.2) uses a
separate mechanism from `X-API-Key`: an `X-Webhook-Signature` header holding
an HMAC-SHA256 digest of the raw request body, keyed by the `WEBHOOK_SECRET`
env var (`app/core/auth.py`'s `require_webhook_signature`). Same shape and
same limitations as the API key above — one shared secret, no-op if unset
(local dev only), constant-time comparison via `hmac.compare_digest`.

## Rate limiting

`/api` routes (products, inventory, forecast — anything behind
`require_api_key`) are rate-limited via `slowapi`
(`app/core/rate_limit.py`), keyed by `X-API-Key` when present, else client
IP. Default limit is `100/minute`, configurable via the `RATE_LIMIT` env
var. Limit exceeded returns `429`. `/health`, `/metrics`, and
`/api/webhooks/ingest` (signature-verified, separate trust boundary — see
below) are exempt.

## Response security headers

Every response gets `X-Content-Type-Options: nosniff`, `X-Frame-Options:
DENY`, and `Referrer-Policy: no-referrer` (`app/core/security_headers.py`).
`Strict-Transport-Security` is added only when the request arrived over
HTTPS (detected via `X-Forwarded-Proto`, set by both Caddy and AWS's ALB) —
uvicorn itself always sees plain HTTP, since TLS is terminated upstream, so
asserting HSTS unconditionally would break local dev and the no-domain
plain-HTTP self-hosted path. Neither Caddy nor the ALB add these headers on
their own; `Caddyfile` is a bare `reverse_proxy`.

## Dashboard access

The Streamlit dashboard (`dashboard/app.py`) talks to the database directly
via the service layer — it doesn't go through `/api` and has none of the
`X-API-Key` protection above. It has no auth of its own at all. In the
self-hosted deployment path, its container port is never published by
default; it's only reachable once the Caddy overlay
(`docker-compose.caddy.yml`) fronts it with HTTP basic auth on a dedicated
HTTPS listener (`https://<DOMAIN>:8501`) — see
[`docs/deployment/self-hosted.md`](docs/deployment/self-hosted.md). Same
caveat as above: basic auth here is one shared username/password, not
per-user identity.

## Prior security review

[`docs/archive/report.md`](docs/archive/report.md) is a point-in-time AI code
review from an earlier stage of the project. Most of its findings have since
been addressed (see the commit history around `feat(auth)`), but it's kept as
project history rather than updated in place — it's not a live status report.
