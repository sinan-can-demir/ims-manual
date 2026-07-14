# IMS — Inventory Management System
Author: Sinan Demir
Last Updated: 2026-04-01

This roadmap organizes the development of IMS into **epochs**.
Each epoch unlocks the next capability. The system evolves from a simple
backend into a full data platform with ML and a dashboard.

Core principles:
- Events are the **source of truth**
- Schemas are **contracts**
- Pipelines must be **reproducible**
- ML depends on **data quality**

------------------------------------------------------------
EPOCH 0 — Foundations
------------------------------------------------------------

Goal: Create a minimal, reproducible backend environment.

[x] Project structure
[x] FastAPI backend
[x] PostgreSQL database
[x] Docker environment (with Fedora :Z volume fix)
[x] SQLAlchemy models
[x] Event-driven inventory schema
[x] Inventory projection (inventory_state)
[x] Alembic migrations setup

Milestone: Complete
- Database schema versioned with Alembic
- Tables: products, inventory_events, inventory_state, alembic_version
- Docker startup runs migrations automatically before serving

------------------------------------------------------------
EPOCH 1 — Event-Driven Backend
------------------------------------------------------------

Goal: Build a robust, production-hardened event-driven inventory system.

[x] Add event table indexes (product_id, created_at, composite)
[x] Enforce product_id NOT NULL in inventory_events
[x] Add idempotency key (event_id) to inventory events
[x] Quantity normalization per event type
[x] Oversell protection (inventory cannot go below 0)
[x] SELECT FOR UPDATE concurrency safety on inventory_state row
[x] Inventory read from projection, not SUM(events)
[x] Event writes and projection updates in single transaction
[x] Duplicate SKU returns 409 Conflict
[x] Pydantic v2 migration (ConfigDict, no deprecation warnings)
[x] Structured JSON logging (app/core/logging.py)
[x] Event replay service (rebuild_inventory_state from events)
[x] Integration tests (pytest with SQLite StaticPool in-memory DB)
[x] Test isolation (tables created/dropped per function fixture)
[x] Shared test utility (tests/utils.py)
[x] Makefile targets (up, down, reset, logs, test, test-e2e, migrate, shell)
[x] E2E bash test script (test_scripts/test_sc.sh)
[x] Response models and correct status codes (201 for POST)
[x] Deterministic event ordering (ORDER BY created_at ASC, id ASC)
[x] Pagination on event listing endpoint (limit, offset)
[x] Edge case tests (return/damage sequence, large adjustments)
[x] README accurate and synced with actual endpoints

Milestone: Complete

------------------------------------------------------------
EPOCH 2 — Batch Data Platform
------------------------------------------------------------

Goal: Export the event log into a partitioned data lake.

[x] data_lake/ directory and inventory_events/ subfolder
[x] .gitignore excludes parquet files and checkpoints.json
[x] Export service (export_service.py)
[x] Query events ordered by (created_at, id)
[x] Partition by year/month/day
[x] Write partitioned .parquet files
[x] Incremental export using checkpoints.json
[x] Full and incremental export modes
[x] POST /api/inventory/export endpoint
[x] Validation script (validate_exports.py)
[x] CLI script (app/scripts/export_events.py)
[x] pytest tests for export service
[x] Handle timezone-naive datetimes from SQLite in tests
[x] Makefile target: make export

Milestone: Complete

------------------------------------------------------------
EPOCH 3 — Data Warehouse
------------------------------------------------------------

Goal: Build an analytical layer on top of the data lake using DuckDB.

[x] DuckDB installed and reading Parquet files
[x] Star schema design (fact + dimensions)
[x] dim_products built from PostgreSQL
[x] dim_dates pre-generated for full date range
[x] fact_inventory_events joined from data lake
[x] Three analytical queries documented (warehouse/queries.sql)
[x] CLI script (app/scripts/build_warehouse.py)
[x] Makefile target: make warehouse
[x] Warehouse tests (test_warehouse.py)
[x] warehouse/README.md documents schema and rebuild steps

Milestone: Complete

------------------------------------------------------------
EPOCH 4 — dbt Transformations
------------------------------------------------------------

Goal: Replace hand-written Python warehouse service with dbt models.

[x] dbt-duckdb installed and configured
[x] dbt project initialized (warehouse/ims_warehouse/)
[x] profiles.yml configured for DuckDB
[x] Sources declared (sources.yml)
[x] Staging model (stg_inventory_events.sql)
[x] Dimension models (dim_products.sql, dim_dates.sql)
[x] Fact model (fact_inventory_events.sql)
[x] Schema tests (unique, not_null, relationships)
[x] dbt docs generated
[x] Makefile targets: make dbt-run, make dbt-test, make dbt-docs
[x] warehouse_service.py deprecated with clear comment

Milestone: Complete

------------------------------------------------------------
EPOCH 5 — ML Platform
------------------------------------------------------------

Goal: Enable demand forecasting and restock recommendations.

[x] Feature engineering service (feature_service.py)
[x] daily_sales feature table (product_id, date, units_sold, rolling_avg_7d)
[x] Prophet model training per product (forecast_service.py)
[x] Model persistence (models/prophet_{product_id}.pkl)
[x] Forecast API endpoint (GET /api/forecast/{product_id})
[x] Restock recommendation service (restock_service.py)
[x] Restock API endpoint (GET /api/restock/{product_id})
[x] Urgency classification (OK / LOW / URGENT / STOCKOUT)
[x] Pydantic schemas for forecast and restock responses
[x] CLI scripts: make features, make train
[x] Seed data script (scripts/seed_data.py)
[x] Synthetic feature generator (scripts/generate_synthetic_features.py)
[x] Forecast and restock tests (test_forecast.py)

Milestone: Complete

------------------------------------------------------------
EPOCH 6 — Application Layer (Dashboard)
------------------------------------------------------------

Goal: Build an interactive inventory dashboard with Streamlit.

[x] Streamlit installed and configured
[x] dashboard/app.py with full layout
[x] Product selector (sidebar dropdown)
[x] Inventory metrics (current stock, projected demand, recommended order)
[x] Restock alert with urgency color coding
[x] 7-day demand forecast chart with confidence band (Plotly)
[x] Recent inventory events table
[x] Cached data loaders (@st.cache_data with TTL)
[x] Loading spinners and empty state handling
[x] Makefile target: make dashboard

Milestone: Complete

------------------------------------------------------------
EPOCH 7 — Production Hardening & AWS Deployment (Next)
------------------------------------------------------------

Goal: Make the system production-grade and deploy it to AWS.  

Phase 1 — Quick wins (no architecture changes)  
[x] Pin all dependency versions in requirements.txt  
[x] Add /health endpoint to FastAPI app (required by AWS ALB/ECS)  
[x] Add CORS middleware to FastAPI app (origins via CORS_ORIGINS env var)  
[x] Add .env.example documenting all required environment variables  
[x] Fix docker-compose: add Postgres healthcheck, remove fragile sleep 3  
[x] Tune SQLAlchemy connection pool for cloud (pool_pre_ping, pool_size, max_overflow)  

Phase 2 — Security hardening  
[ ] Remove hardcoded credentials from docker-compose.yml and database.py defaults  
[ ] Add API authentication (API key header or JWT via FastAPI middleware)  
[ ] Add non-root USER to Dockerfile  
[ ] Stop leaking internal error details (replace str(e) in forecast.py 500 responses)  

Phase 3 — App hardening  
[ ] Raise domain exceptions in service layer instead of HTTPException
      (InsufficientInventoryError, ProductNotFoundError → converted at API layer)  
[ ] Run Uvicorn with multiple workers in production (Gunicorn + UvicornWorker)  
[ ] Improve Dockerfile: multi-stage build, proper .dockerignore, non-root user  

Phase 4 — Testing  
[ ] Run integration tests against a real Postgres instead of SQLite
      (SELECT FOR UPDATE is silently ignored in SQLite — concurrency tests are not valid)  
[ ] Add CI/CD via GitHub Actions (make repo public first for free CI)  
      - Run pytest on every push/PR  
      - Build and lint Docker image  

Phase 5 — Deployment (self-hosted + AWS)  
Two paths, not one — being open-source, the default should be the cheapest
and most portable option, with AWS available for teams that already run
there. See README.md's "Deployment" section.

Self-hosted (default, docs/deployment/self-hosted.md):  
[x] docker-compose.prod.yml — prod hardening overlay (no dev bind-mount,
      no exposed DB port, fail-loud on missing secrets)  
[x] docker-compose.caddy.yml — optional automatic HTTPS via Caddy  
[x] Self-hosted deployment guide  
[ ] Move data lake from local filesystem to object storage (S3-compatible —
      evaluate MinIO or a provider's S3-compatible bucket, not AWS-only)  
[ ] Deploy dashboard alongside the API in the self-hosted stack  

AWS (enterprise, infra/README.md):  
[~] Configure AWS infrastructure (ECS Fargate, RDS PostgreSQL, ALB) — Terraform written (infra/), not yet applied  
[~] Store secrets in AWS Secrets Manager, inject as environment variables — wired in Terraform, not yet applied  
[~] Wire CloudWatch Logs — wired in Terraform, not yet applied  
[ ] Move data lake from local filesystem to S3  
[ ] Deploy dashboard (Streamlit on ECS, read feature store from S3)  
[ ] Set up domain + HTTPS via ACM + ALB  

Milestone: App deployable via either path with real auth, secrets management, and CI/CD  

------------------------------------------------------------
EPOCH 8 — Kafka Streaming (Optional)
------------------------------------------------------------

Goal: Process inventory events in real time via Kafka.

[ ] Kafka + Zookeeper via Docker Compose  
[ ] Event producer (FastAPI publishes to Kafka after DB write)  
[ ] Projection updater consumer  
[ ] Data lake writer consumer  
[ ] Deduplication on consumer side  
[ ] Replay via compacted topic  

------------------------------------------------------------
EPOCH 9 — Advanced ML (Optional)
------------------------------------------------------------

Goal: Productionize the ML layer.  

[ ] Automated retraining pipeline  
[ ] Model versioning  
[ ] Feature importance analysis  
[ ] A/B testing framework for models  

------------------------------------------------------------
Full Pipeline (Current)
------------------------------------------------------------

make up          → start Docker stack  
make migrate     → apply Alembic migrations  
make test        → run pytest suite  
make test-e2e    → run bash E2E tests  
make export      → export events to data lake  
make dbt-run     → build warehouse models  
make features    → build feature store  
make train       → train Prophet models  
make dashboard   → start Streamlit dashboard at localhost:8501  

------------------------------------------------------------
Long-Term Vision
------------------------------------------------------------

Simple CRUD API
        ↓
Event-Driven System       ✅ Complete
        ↓
Batch Data Platform       ✅ Complete
        ↓
Data Warehouse (dbt)      ✅ Complete
        ↓
ML Platform               ✅ Complete
        ↓
Application Layer         ✅ Complete
        ↓
Production Hardening      ← Next
        ↓
Kafka Streaming           ← Optional
        ↓
ML-Driven Intelligence    ← Future