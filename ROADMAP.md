# IMS — Inventory Management System
Author: Sinan Demir
Last Updated: 2026-03-24

This roadmap organizes the development of IMS (Inventory Management System) into **epochs**.
Each epoch unlocks the next capability. The system evolves from a simple backend into a full
data platform with streaming and ML.

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

Milestone Achieved:
- Database schema versioned with Alembic
- Initial migration created and applied
- Tables: products, inventory_events, inventory_state, alembic_version
- Docker startup runs migrations automatically before serving


------------------------------------------------------------
EPOCH 1 — Event-Driven Backend
------------------------------------------------------------

Goal: Build a robust, production-hardened event-driven inventory system.

[x] Add event table indexes (product_id, created_at, composite)
[x] Enforce product_id NOT NULL in inventory_events
[x] Add idempotency key (event_id) to inventory events
[x] Quantity normalization per event type (PURCHASE/RETURN = positive, SALE/DAMAGE = negated internally)
[x] Oversell protection (inventory cannot go below 0)
[x] SELECT FOR UPDATE concurrency safety on inventory_state row
[x] Inventory read from projection (inventory_state), not SUM(events)
[x] Event writes and projection updates in single transaction (atomicity)
[x] Duplicate SKU returns 409 Conflict
[x] Pydantic v2 migration (ConfigDict, no deprecation warnings)
[x] Structured logging (app/core/logging.py)
[x] Event replay service (rebuild_inventory_state from events)
[x] Integration tests (pytest with SQLite StaticPool in-memory DB)
[x] Test isolation (tables created/dropped per function fixture)
[x] Shared test utility (tests/utils.py with create_product helper)
[x] Makefile targets (up, down, reset, logs, test, test-e2e, test-all, migrate, shell)
[x] E2E bash test script (test_scripts/test_sc.sh with Docker lifecycle)
[x] Response models and correct status codes (201 for POST)
[x] Deterministic event ordering (ORDER BY created_at ASC, id ASC)
[x] README accurate and synced with actual endpoints

In Progress / Remaining:
[ ] Pagination on event listing endpoint (limit, offset params)
[ ] Test: concurrent sales do not oversell (requires threads or async simulation)
[ ] Test: return → damage sequence
[ ] Test: large adjustment edge cases
[ ] Refactor: remove ORM object creation from product route (minor cleanup)
[ ] Structured logging: JSON format output (currently plain text)
[ ] Correlation / request IDs in logs


------------------------------------------------------------
EPOCH 2 — Batch Data Platform
------------------------------------------------------------

Goal: Export the event log into a partitioned data lake.

Infrastructure:
[x] data_lake/ directory and inventory_events/ subfolder
[x] .gitignore excludes parquet files and checkpoints.json
[x] data_lake/README.md documents structure and design principles

Export Service (app/services/export_service.py):
[x] Query events ordered by (created_at, id)
[x] Convert to pandas DataFrame
[x] Partition by year/month/day
[x] Write partitioned .parquet files
[x] Incremental export using checkpoints.json
[x] Full and incremental export modes

Export API:
[x] POST /api/inventory/export endpoint
[x] Returns ExportMetadata schema (rows, partitions, files, mode, checkpoint_updated)

Validation Script (app/scripts/validate_exports.py):
[x] Row count comparison (DB vs parquet)
[x] Duplicate event_id detection
[x] Schema column validation

CLI Script:
[x] python app/scripts/export_events.py (runs incremental export)

Remaining:
[ ] pytest tests for export service (file creation, partition structure, incremental logic)
[ ] Logging: log export start, completion, rows exported, partition counts
[ ] Handle timezone-naive datetimes from SQLite during testing (test environment gap)
[ ] Make export idempotent (re-running same export does not duplicate rows in parquet)
[ ] Makefile target: make export

Milestone Definition (Epoch 2 COMPLETE when):
[ ] Events exported to partitioned Parquet
[ ] Incremental export working and tested
[ ] Pipeline reproducible from scratch
[ ] Data validated (row counts match, no duplicates, schema consistent)


------------------------------------------------------------
EPOCH 3 — Data Warehouse
------------------------------------------------------------

Goal: Build an analytics layer on top of the data lake.

[ ] Choose warehouse approach (DuckDB local vs hosted Postgres schema vs dbt)
[ ] Create warehouse schema
[ ] Build fact_inventory_events (cleaned, typed, partitioned view)
[ ] Build dim_products (product dimension table)
[ ] Build dim_dates (date dimension table)
[ ] Create analytical metrics (daily stock levels, event counts, turnover rate)
[ ] Add dbt project (if chosen): models, tests, documentation

Warehouse Target Schema:

    fact_inventory_events
    dim_products
    dim_dates


------------------------------------------------------------
EPOCH 4 — Streaming Platform
------------------------------------------------------------

Goal: Process inventory events in real time.

[ ] Introduce Kafka (local via Docker Compose)
[ ] Create event producer (FastAPI publishes events to Kafka after writing to DB)
[ ] Create event consumers (projection updater, data lake writer)
[ ] Implement replay via Kafka compacted topic or event log
[ ] Deduplication logic on consumer side

Architecture:

    FastAPI → Kafka → Consumers → Projections / Data Lake


------------------------------------------------------------
EPOCH 5 — ML Platform
------------------------------------------------------------

Goal: Enable forecasting and anomaly detection.

[ ] Create feature tables (daily_sales, rolling_avg_7d, stockout_frequency)
[ ] Build demand forecasting model (ARIMA or Prophet baseline)
[ ] Detect inventory anomalies (sudden drops, abnormal events)
[ ] Build restock recommendation system
[ ] Automate training pipeline (Airflow or simple cron)


------------------------------------------------------------
EPOCH 6 — Application Layer
------------------------------------------------------------

Goal: Create operational dashboards and tools.

[ ] Admin dashboard (FastAPI + lightweight frontend or Streamlit)
[ ] Inventory monitoring (current stock, low stock alerts)
[ ] Alerting system (email or webhook on threshold breach)
[ ] Reporting UI (event history, stock trends)


------------------------------------------------------------
EPOCH 7 — Advanced Automation (Optional)
------------------------------------------------------------

Goal: Intelligent inventory automation.

[ ] Auto-order recommendations
[ ] Supplier lead-time prediction
[ ] Warehouse sensor integration
[ ] Smart alerts


------------------------------------------------------------
Daily Development Workflow
------------------------------------------------------------

Schema changes:

1. Modify SQLAlchemy models
2. Generate migration:
   alembic revision --autogenerate -m "description"
   (run inside Docker: docker compose exec api alembic ...)
3. Inspect migration file in migrations/versions/
4. Apply migration:
   alembic upgrade head

Running tests:

    make test          # pytest (fast, SQLite in-memory)
    make test-e2e      # bash E2E against Docker stack
    make test-all      # both

Exporting data:

    python app/scripts/export_events.py


------------------------------------------------------------
Long-Term Vision
------------------------------------------------------------

IMS evolves from:

    Simple CRUD API
            ↓
    Event-Driven System  ← current
            ↓
    Batch Data Platform  ← in progress
            ↓
    Streaming System
            ↓
    ML-Driven Inventory Intelligence
