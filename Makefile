# 📦 IMS Makefile

.PHONY: up down reset rebuild logs seed export warehouse dbt-run dbt-test dbt-docs \
        features train test test-e2e test-all test-clean migrate shell dashboard lint format

# Always use the project's own venv, never whatever's first on PATH —
# running these bare broke silently (dbt/joblib "not found") whenever the
# venv wasn't manually activated first.
PYTHON := .venv/bin/python
DBT    := .venv/bin/dbt

# -------------------------
# Dev lifecycle
# -------------------------
up:
	docker compose up

up-d:
	docker compose up -d

down:
	docker compose down

# data_lake/, feature_store/, warehouse/, and models/ are local files, not
# Docker volumes — `down -v` wipes the DB but leaves these stale. A stale
# checkpoint.json in particular makes the next `make export` skip freshly
# seeded events (it resumes from the old high-water mark) while old rows
# with now-colliding IDs stay in the parquet files, breaking the dbt
# uniqueness test and starving the feature store. Clear them so a reset
# always starts every downstream stage from a clean slate.
reset:
	docker compose down -v
	rm -rf data_lake/inventory_events/* data_lake/checkpoints.json
	rm -f feature_store/*.parquet
	rm -f warehouse/*.parquet warehouse/ims.duckdb
	rm -f models/*.pkl
	docker compose up --build

rebuild:
	docker compose up --build

logs:
	docker compose logs -f

# -------------------------
# Application layer
# -------------------------
dashboard:
	.venv/bin/streamlit run dashboard/app.py

# -------------------------
# Database
# -------------------------
migrate:
	docker compose exec api alembic upgrade head

# -------------------------
# Seed data
# -------------------------
seed:
	$(PYTHON) scripts/seed_data.py

# -------------------------
# Export events
# -------------------------
export:
	$(PYTHON) -m app.scripts.export_events

# -------------------------
# Warehouse
# -------------------------
warehouse:
	$(PYTHON) -m app.scripts.build_warehouse

# -------------------------
# dbt
# -------------------------
dbt-run:
	cd warehouse/ims_warehouse && ../../$(DBT) run

dbt-test:
	cd warehouse/ims_warehouse && ../../$(DBT) test

dbt-docs:
	cd warehouse/ims_warehouse && ../../$(DBT) docs generate && ../../$(DBT) docs serve

# -------------------------
# Features
# -------------------------
features:
	$(PYTHON) -m app.scripts.build_features

# -------------------------
# Train
# -------------------------
train:
	$(PYTHON) -m app.scripts.train_model

# -------------------------
# Shell access
# -------------------------
shell:
	docker compose exec api sh

# -------------------------
# Pytest (fast tests)
# -------------------------
test:
	.venv/bin/pytest

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

# -------------------------
# Lint / format
# -------------------------
lint:
	.venv/bin/ruff check .

format:
	.venv/bin/ruff format .