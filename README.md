# IMS — Inventory Management System

An event-driven inventory platform with a full analytics pipeline and ML-powered demand forecasting. Built from scratch as a learning project covering data engineering, backend systems, and machine learning.

**Stack:** FastAPI · PostgreSQL · dbt · DuckDB · Prophet · Streamlit · Docker

---

## What it does

- Tracks inventory changes as an **immutable event log** (event sourcing + CQRS)
- Exports events to a **Parquet data lake**, transforms them in a **DuckDB warehouse** via dbt
- Trains a **Prophet forecasting model** per product on historical demand
- Serves a **Streamlit dashboard** with live inventory levels, event history, and 30-day demand forecasts

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      WRITE PATH                              │
│   Client → POST /api/inventory/events                        │
│          → inventory_events (append-only)                    │
│          → inventory_state  (projection, same transaction)   │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      READ PATH                               │
│   Client → GET /api/inventory/{product_id}                   │
│          → inventory_state (O(1) pre-computed projection)    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                   ANALYTICS PIPELINE                         │
│   PostgreSQL → Parquet (data lake)                           │
│             → DuckDB  (warehouse)                            │
│             → dbt     (dim/fact models + data quality tests) │
│             → Prophet (demand forecast per product)          │
│             → Streamlit dashboard                            │
└──────────────────────────────────────────────────────────────┘
```

### Core concepts

| Concept | Description |
|---|---|
| `InventoryEvent` | Immutable ledger entry for every stock change |
| `InventoryState` | Pre-computed projection — reads are O(1), no aggregation at query time |
| `event_id` | Client-provided UUID for idempotent writes |
| dbt models | Dimensional warehouse (products, dates, daily snapshots) built on DuckDB |
| Feature store | Lag features + rolling averages prepared for ML training |
| Prophet model | Per-product demand forecasting with 30-day horizon |

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| Database | PostgreSQL 15 + SQLAlchemy + Alembic |
| Validation | Pydantic |
| Data lake | Parquet files |
| Warehouse | DuckDB + dbt |
| ML | Prophet (Meta) |
| Dashboard | Streamlit |
| Containerization | Docker + Docker Compose |
| Testing | Pytest + httpx |

---

## Project Structure

```
ims-manual/
├── app/                    # FastAPI application
│   ├── api/                # Route handlers (products, inventory)
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   └── services/           # Business logic
├── migrations/             # Alembic migrations
├── tests/                  # Unit, integration, and e2e tests
├── pipelines/              # PostgreSQL → Parquet export
├── data_lake/              # Parquet event snapshots
├── warehouse/              # DuckDB + dbt project
│   └── ims_warehouse/
│       ├── models/         # dbt dim/fact models
│       └── tests/          # dbt data quality tests
├── feature_store/          # Engineered features for ML
├── models/                 # Trained Prophet model artifacts (gitignored — run `make train` to generate)
├── dashboard/              # Streamlit app
├── docker/                 # Dockerfile
├── docker-compose.yml
├── Makefile                # One-command dev workflow
└── requirements.txt
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose

### Quickstart (Docker)

```bash
# Start PostgreSQL + API
make up

# Run migrations
make migrate

# Seed some data, then run the full pipeline
make export       # PostgreSQL → Parquet
make warehouse    # build DuckDB warehouse tables
make dbt-run      # run dbt transformations
make dbt-test     # run data quality tests
make features     # build feature store
make train        # train Prophet models

# Launch dashboard
streamlit run dashboard/app.py
```

### Local Development (no Docker)

```bash
pip install -r requirements.txt
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/ims"
alembic upgrade head
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`.

---

## API Reference

### Products

```http
POST /api/products
{ "name": "Widget A", "sku": "WGT-001" }
```

### Inventory Events

```http
POST /api/inventory/events
{
    "product_id": 1,
    "event_type": "PURCHASE",
    "quantity": 100,
    "event_id": "evt-uuid-123"
}
```

| Event Type | Effect | Notes |
|---|---|---|
| `PURCHASE` | +quantity | Stock received |
| `SALE` | -quantity | Oversell protected |
| `DAMAGE` | -quantity | Oversell protected |
| `RETURN` | +quantity | Customer return |
| `ADJUSTMENT` | ±quantity | Manual correction |

```http
GET /api/inventory/{product_id}       # current stock level
GET /api/inventory/events/{product_id} # full event history
```

---

## Testing

```bash
make test          # unit + integration tests
make test-e2e      # end-to-end (requires Docker)
make test-all      # everything

pytest --cov=app tests/  # with coverage
```

| Test file | Coverage |
|---|---|
| `test_products.py` | Product creation, SKU uniqueness |
| `test_inventory.py` | Core inventory flow, oversell protection |
| `test_inventory_validation.py` | Input validation per event type |
| `test_idempotency.py` | Duplicate event handling |

---

## Makefile Reference

```bash
make up           # start services
make down         # stop services
make reset        # full reset (destroys data)
make migrate      # apply Alembic migrations
make logs         # tail API logs
make shell        # shell into API container
make export       # export events → Parquet data lake
make warehouse    # build DuckDB warehouse
make dbt-run      # run dbt models
make dbt-test     # run dbt data quality tests
make features     # build feature store
make train        # train Prophet models
make test         # run tests
make test-e2e     # run e2e tests
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/ims` | PostgreSQL connection |
| `PYTHONPATH` | `/app` | Python module path |

Copy `.env.example` to `.env` and adjust as needed.

---

## Roadmap

| Epoch | Focus | Status |
|---|---|---|
| 0 | Foundations | ✅ Complete |
| 1 | Event-Driven Backend (CQRS + event sourcing) | ✅ Complete |
| 2 | Batch Data Pipeline (Parquet data lake) | ✅ Complete |
| 3 | Data Warehouse (DuckDB + dbt) | ✅ Complete |
| 4 | Feature Engineering | ✅ Complete |
| 5 | ML Platform (Prophet forecasting) | ✅ Complete |
| 6 | Streamlit Dashboard | ✅ Complete |
| 7 | Production Hardening + AWS Deployment | In Progress |

---

## License

[MIT](LICENSE)

## Author

**Sinan Demir** — Computer Science @ University of Texas at Dallas
