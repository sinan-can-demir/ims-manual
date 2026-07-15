FROM python:3.11-slim

WORKDIR /app

# curl is needed by the HEALTHCHECK below; not present in the slim base image.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

# UID 1000 matches the default first-user UID on most Linux distros
# (including Fedora), so the dev bind-mount in docker-compose.yml stays
# writable without needing a matching --user override.
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]