# 📦 IMS Makefile

.PHONY: up down reset rebuild logs test test-e2e test-all test-clean migrate shell

# -------------------------
# Dev lifecycle
# -------------------------
up:
	docker compose up

up-d:
	docker compose up -d

down:
	docker compose down

reset:
	docker compose down -v
	docker compose up --build

rebuild:
	docker compose up --build

logs:
	docker compose logs -f

# -------------------------
# Database
# -------------------------
migrate:
	docker compose exec api alembic upgrade head

# -------------------------
# Shell access
# -------------------------
shell:
	docker compose exec api sh

# -------------------------
# Pytest (fast tests)
# -------------------------
test:
	pytest

# -------------------------
# E2E System Test (Docker)
# -------------------------
test-e2e:
	sh test_scripts/test_sc.sh

# -------------------------
# Full pipeline
# -------------------------
test-all:
	make test
	make test-e2e

# -------------------------
# Cleanup
# -------------------------
test-clean:
	rm -rf .pytest_cache