# Self-Hosted Deployment

The recommended way to run IMS for real use — no cloud account, no vendor
lock-in, ~$5-20/month on any VPS. Built entirely on the Docker Compose setup
already used for local development, plus [Caddy](https://caddyserver.com/)
(open-source, automatic HTTPS) if you have a domain.

Looking for an AWS/enterprise deployment instead? See
[`infra/README.md`](../../infra/README.md).

## Prerequisites

- A VPS with Docker + the Compose plugin installed. Any provider works —
  Hetzner, DigitalOcean, OVH, a spare machine at home, etc. A 1-2 vCPU /
  2-4GB RAM box is plenty to start.
- (Optional) A domain name, if you want HTTPS via Caddy. Not required —
  you can run over plain HTTP first and add this later.

## 1. Get Docker onto the server

Most providers offer a "Docker" marketplace image that comes with this
preinstalled. Otherwise, on a fresh Debian/Ubuntu box:

```bash
curl -fsSL https://get.docker.com | sh
```

## 2. Clone the repo and configure

```bash
git clone https://github.com/sinan-can-demir/ims-manual.git
cd ims-manual
cp .env.example .env
```

Edit `.env` and set, at minimum:
- `POSTGRES_PASSWORD` — a real password (the compose config refuses to
  start without one; there's no insecure default in production mode)
- `API_KEY` — generate with `openssl rand -hex 32`. Leaving this unset
  disables auth entirely, which is fine for local dev but **not** for
  anything reachable on the open internet — see
  [`SECURITY.md`](../../SECURITY.md).
- `CORS_ORIGINS` — if you're also running the dashboard, point this at
  wherever it's served from.

## 3. Start the stack

**Without a domain (plain HTTP):**

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

The API is now reachable at `http://<server-ip>:8000`.

**With a domain (automatic HTTPS via Caddy):**

Point an A record for your domain at the server's public IP first, then also
set `DOMAIN=your-domain.com` in `.env`:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.caddy.yml up -d --build
```

Caddy requests and renews a Let's Encrypt certificate automatically — no
manual cert management. The API is now reachable at `https://your-domain.com`.

In both modes, `docker-compose.prod.yml` also: runs the built image only (no
live source bind-mount), restarts containers automatically on crash/reboot
(`restart: unless-stopped`), and stops publishing Postgres's port to the
outside world — only the `api` container can reach it, over the internal
Docker network.

## 4. Verify

```bash
curl http://<server-ip>:8000/health          # or https://your-domain.com/health
curl -H "X-API-Key: <your key>" http://<server-ip>:8000/api/products
```

## Updating

```bash
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml [-f docker-compose.caddy.yml] up -d --build
```

Migrations run automatically on container start (same `alembic upgrade head`
step as local dev).

## Backups

The Postgres data lives in the `postgres_data` named volume. A simple
periodic dump:

```bash
docker compose exec db pg_dump -U postgres ims > backup-$(date +%F).sql
```

Copy that file off the server (e.g. to object storage, or just `scp` it
somewhere) on whatever schedule matters to you — a cron job calling the
above is enough for most self-hosted use.

## What this doesn't cover yet

The data pipeline (Parquet data lake, DuckDB warehouse, dbt, Prophet
training) and the Streamlit dashboard are still local-filesystem/manual-CLI
concerns on this path — same as in local dev, just run via `make export` /
`make warehouse` / etc. inside the server, or over SSH. See `ROADMAP.md` for
what's planned for those.
