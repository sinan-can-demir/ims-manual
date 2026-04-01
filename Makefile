# 📦 IMS Makefile

.PHONY: up down reset rebuild logs test test-e2e test-all test-clean migrate shell warehouse train

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
# Export events
# -------------------------
export:
	python -m app.scripts.export_events

# -------------------------
# Warehouse
# -------------------------
warehouse:
	python -m app.scripts.build_warehouse

# -------------------------
# dbt
# -------------------------
dbt-run:
	cd warehouse/ims_warehouse && dbt run

dbt-test:
	cd warehouse/ims_warehouse && dbt test

dbt-docs:
	cd warehouse/ims_warehouse && dbt docs generate && dbt docs serve

# -------------------------
# Features
# -------------------------
features:
	python -m app.scripts.build_features

# -------------------------
# Train
# -------------------------
train:
	python -m app.scripts.train_model

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