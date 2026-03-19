# IMS — Inventory Management System
Author: Sinan Demir
Last Updated: 2026-03-19

This roadmap organizes the development of IMS (Inventory Management System) into **epochs**.
Each epoch unlocks the next capability. The system evolves from a simple backend into a full
data platform with streaming and ML.

Core principles:
- Events are the **source of truth**
- Schemas are **contracts**
- Pipelines must be **reproducible**
- ML depends on **data quality**

I am learning along the way so this is beyond what I can do for this time, but I am working on it.

------------------------------------------------------------
EPOCH 0 — Foundations
------------------------------------------------------------

Goal: Create a minimal, reproducible backend environment.

[x] Project structure
[x] FastAPI backend
[x] PostgreSQL database
[x] Docker environment
[x] SQLAlchemy models
[x] Event-driven inventory schema
[x] Inventory projection (inventory_state)
[x] Alembic migrations setup

Milestone Achieved:
- Database schema versioned with Alembic
- Initial migration created
- Tables:
    products
    inventory_events
    inventory_state
    alembic_version


------------------------------------------------------------
EPOCH 1 — Event‑Driven Backend
------------------------------------------------------------

Goal: Build a robust event‑driven inventory system.

[x] Add event table indexes
[x] Enforce product_id NOT NULL in events
[x] Add idempotency key to events
[x] Improve projection logic
[ ] Add event replay capability
[ ] Add structured logging
[x] Add integration tests

Features:
- InventoryEvent = source of truth
- InventoryState = projection
- Oversell protection


------------------------------------------------------------
EPOCH 2 — Batch Data Platform
------------------------------------------------------------

Goal: Export events into a data lake.

[ ] Create event export job
[ ] Write events to Parquet
[ ] Partition by date
[ ] Implement incremental export
[ ] Build reproducible pipelines

Structure:

data_lake/
    inventory_events/
        year=YYYY/
        month=MM/
        day=DD/


------------------------------------------------------------
EPOCH 3 — Data Warehouse
------------------------------------------------------------

Goal: Build analytics layer.

[ ] Create warehouse schema
[ ] Build fact_inventory_events
[ ] Build dimension tables
[ ] Create analytical metrics
[ ] Add dbt transformations

Warehouse Example:

fact_inventory_events
dim_products
dim_dates


------------------------------------------------------------
EPOCH 4 — Streaming Platform
------------------------------------------------------------

Goal: Process events in real time.

[ ] Introduce Kafka
[ ] Create event producer
[ ] Create event consumers
[ ] Implement replay
[ ] Deduplication logic

Architecture:

FastAPI → Kafka → Consumers → Projections


------------------------------------------------------------
EPOCH 5 — ML Platform
------------------------------------------------------------

Goal: Enable forecasting and anomaly detection.

[ ] Create feature tables
[ ] Build demand forecasting model
[ ] Detect inventory anomalies
[ ] Build recommendation system
[ ] Automate training pipeline

Example ML features:

daily_sales
rolling_avg_7d
stockout_frequency


------------------------------------------------------------
EPOCH 6 — Application Layer
------------------------------------------------------------

Goal: Create operational dashboards and tools.

[ ] Admin dashboard
[ ] Inventory monitoring
[ ] Alerting system
[ ] Stock check tasks for employees
[ ] Reporting UI


------------------------------------------------------------
EPOCH 7 — Advanced Automation (Optional)
------------------------------------------------------------

Goal: Intelligent inventory automation.

[ ] Auto‑order recommendations
[ ] Supplier lead‑time prediction
[ ] Warehouse sensor integration
[ ] Smart alerts


------------------------------------------------------------
Daily Development Workflow
------------------------------------------------------------

Schema changes:

1. Modify SQLAlchemy models
2. Generate migration
   alembic revision --autogenerate -m "description"
3. Inspect migration file
4. Apply migration
   alembic upgrade head


------------------------------------------------------------
Long‑Term Vision
------------------------------------------------------------

IMS evolves from:

Simple CRUD API
        ↓
Event‑Driven System
        ↓
Data Platform
        ↓
Streaming System
        ↓
ML‑Driven Inventory Intelligence


