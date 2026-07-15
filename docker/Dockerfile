# ---- builder: install deps into an isolated venv, nothing else survives ----
FROM python:3.11-slim AS builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- final: runtime image only, no pip cache / apt lists / build layer ----
FROM python:3.11-slim

WORKDIR /app

# curl is needed by the HEALTHCHECK below; not present in the slim base image.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY . .

ENV PYTHONPATH=/app

# UID 1000 matches the default first-user UID on most Linux distros
# (including Fedora), so the dev bind-mount in docker-compose.yml stays
# writable without needing a matching --user override.
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Plain single-worker Uvicorn by default — matches what docker-compose.yml's
# dev command and docker-compose.prod.yml/infra/ecs.tf's production commands
# all explicitly override anyway. Production paths run Gunicorn with
# UvicornWorker instead (see docker-compose.prod.yml, infra/ecs.tf); this is
# just a sane default for anyone running the image directly.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
