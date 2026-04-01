# IMS — Inventory Management System

A high-performance, event-driven inventory management system built with FastAPI and PostgreSQL. IMS tracks inventory changes through an append-only event log, enabling full auditability, event replay, and analytics capabilities.

This system implements a simplified form of **event sourcing**, where all state changes are recorded as immutable events and projections are derived from them.

I created this system to help small businesses manage their inventory with a modern, professional tool at no cost.

With recent advancements in AI, I wanted to create something meaningful that could integrate with predictive models. This program will evolve to predict estimated restock quantities and dates.

With recent advancements in AI, I wanted to create something meaningful that could integrate with predictive models.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development](#local-development)
  - [Docker Development](#docker-development)
- [API Reference](#api-reference)
  - [Products](#products)
  - [Inventory Events](#inventory-events)
- [Database Schema](#database-schema)
- [Event Types](#event-types)
- [Testing](#testing)
- [Development Workflow](#development-workflow)
- [Environment Variables](#environment-variables)
- [Roadmap](#roadmap)

---

## Features

- **Event-Driven Architecture**: All inventory changes are recorded as immutable events in an append-only ledger
- **CQRS Pattern**: Separate write (events) and read (state projection) paths for optimized performance
- **Idempotent Operations**: Duplicate events are safely handled using event IDs
- **Oversell Protection**: Prevents sales and damage events that exceed available inventory
- **Full Audit Trail**: Complete history of every inventory change with timestamps
- **Event Replay**: Ability to reconstruct inventory state from events at any point in time
- **Database Migrations**: Schema versioning via Alembic for safe migrations
- **Performance**: O(1) inventory reads using projection model
---

## 🧠 Engineering Highlights

- Designed a CQRS-based system with separate write and read models
- Implemented idempotent event handling using unique event IDs
- Built projection-based inventory system for constant-time reads
- Ensured transactional consistency between event log and projection
- Developed full test suite (unit, integration, e2e)
- Containerized system with automated migrations and reproducible setup
- Leveraged AI-assisted development tools to accelerate debugging and design iterations

---

## Architecture

IMS follows the **CQRS (Command Query Responsibility Segregation)** pattern:

```
┌─────────────────────────────────────────────────────────────────┐
│                         WRITE PATH                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Client                                                        │
│      ↓                                                          │
│   POST /api/inventory/events                                    │
│      ↓                                                          │
│   InventoryEvent (append-only ledger)                           │
│      ↓                                                          │
│   Projection Update                                             │
│      ↓                                                          │
│   InventoryState                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          READ PATH                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Client                                                        │
│      ↓                                                          │
│   GET /api/inventory/{product_id}                               │
│      ↓                                                          │
│   InventoryState (pre-computed projection)                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Core Concepts

| Concept | Description |
|---------|-------------|
| **InventoryEvent** | Immutable ledger entry recording a single inventory change |
| **InventoryState** | Current inventory snapshot, derived from events |
| **event_id** | Client-provided unique identifier for idempotency |
| **product_id** | Foreign key linking events to products |

### Inventory Calculation

Inventory is NOT computed at read time.

Instead:

- Events are appended to `inventory_events`
- A projection updates `inventory_state`
- Reads are served from `inventory_state`

This ensures:
- constant-time reads
- no runtime aggregation
- consistency with event log

---

### Projection Consistency

Every write operation:

1. Inserts into `inventory_events`
2. Updates `inventory_state` in the same transaction

This guarantees:
- no divergence between event log and state
- deterministic reconstruction capability

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Web Framework | FastAPI |
| Database | PostgreSQL 15 |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Validation | Pydantic |
| Server | Uvicorn |
| Testing | Pytest + httpx |
| Containerization | Docker + Docker Compose |

---

## Project Structure

```
ims-manual/
├── app/
│   ├── __init__.py
│   ├── main.py                       # FastAPI application entry point
│   ├── database.py                   # SQLAlchemy engine, session, base
│   ├── api/
│   │   ├── products.py               # Product API routes
│   │   └── inventory.py              # Inventory API routes
│   ├── models/
│   │   ├── product.py                # Product SQLAlchemy model
│   │   ├── inventory_event.py        # InventoryEvent model
│   │   ├── inventory_state.py        # InventoryState projection model
│   │   └── enums.py                  # EventType enumeration
│   ├── schemas/
│   │   ├── product.py                # Product Pydantic schemas
│   │   └── inventory_event.py        # InventoryEvent Pydantic schemas
│   └── services/
│       ├── product_service.py        # Product business logic
│       └── inventory_service.py      # Inventory business logic
├── migrations/
│   ├── versions/                     # Alembic migration files
│   ├── env.py                        # Alembic environment configuration
│   └── README                        # Alembic documentation
├── tests/
│   ├── conftest.py                   # Pytest fixtures
│   ├── test_products.py              # Product API tests
│   ├── test_inventory.py             # Core inventory tests
│   ├── test_inventory_validation.py  # Validation tests
│   └── test_idempotency.py           # Idempotency tests
├── docker/
│   └── Dockerfile                    # API container definition
├── docs/                             # Architecture and development notes
├── data_lake/                        # Future: data lake storage
├── pipelines/                        # Future: ETL pipelines
├── docker-compose.yml                # Container orchestration
├── Makefile                          # Development shortcuts
├── alembic.ini                       # Alembic configuration
├── pytest.ini                        # Pytest configuration
├── requirements.txt                  # Python dependencies
├── ROADMAP.md                        # Development roadmap
└── README.md                         # This file
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15 (or Docker)
- Docker & Docker Compose (optional)

### Local Development

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2. Set Up PostgreSQL

Create a PostgreSQL database named `ims`:

```sql
CREATE DATABASE ims;
```

Set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/ims"
```

#### 3. Run Migrations

```bash
alembic upgrade head
```

Or use Make:

```bash
make migrate
```

#### 4. Start the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. API documentation is at `http://localhost:8000/docs`.

### Docker Development

#### Quick Start

```bash
# Start all services (PostgreSQL + API)
make up

# Or in detached mode
make up-d
```

#### Useful Commands

```bash
make logs        # View API logs
make migrate     # Run pending migrations
make shell       # Get shell access to API container
make down        # Stop services
make reset       # Stop and remove volumes (full reset)
make rebuild     # Rebuild and restart services
```

---

## API Reference

All API endpoints are prefixed with `/api`.

### Products

#### Create Product

```http
POST /api/products
Content-Type: application/json

{
    "name": "Widget A",
    "sku": "WGT-001"
}
```

**Response** (201 Created):

```json
{
    "id": 1,
    "name": "Widget A",
    "sku": "WGT-001",
    "created_at": "2026-03-19T10:30:00Z"
}
```

**Error** (409 Conflict) — if SKU already exists:

```json
{
    "detail": "Product with this SKU already exists"
}
```

---

### Inventory Events

#### Record Inventory Event

```http
POST /api/inventory/events
Content-Type: application/json

{
    "product_id": 1,
    "event_type": "PURCHASE",
    "quantity": 100,
    "event_id": "evt-uuid-123"
}
```

**Request Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `product_id` | integer | Yes | ID of the product |
| `event_type` | string | Yes | Type of event (see Event Types) |
| `quantity` | integer | Yes | Quantity (positive for increases, must be positive for PURCHASE/SALE/DAMAGE/RETURN) |
| `event_id` | string | Yes | Unique client-provided ID for idempotency |

**Response** (201 Created):

```json
{
    "id": 1,
    "product_id": 1,
    "event_type": "PURCHASE",
    "quantity": 100,
    "event_id": "evt-uuid-123"
}
```

**Errors**:

| Status | Condition |
|--------|-----------|
| 400 | Invalid quantity (zero, negative for PURCHASE/SALE) or insufficient inventory for SALE/DAMAGE |
| 404 | Product not found |

#### Get Inventory Level

```http
GET /api/inventory/{product_id}
```

**Response** (200 OK):

```json
{
    "product_id": 1,
    "inventory": 85
}
```

#### Get Product Events

```http
GET /api/inventory/events/{product_id}
```

**Response** (200 OK):

```json
[
    {
        "id": 1,
        "product_id": 1,
        "event_type": "PURCHASE",
        "quantity": 100,
        "event_id": "evt-1"
    },
    {
        "id": 2,
        "product_id": 1,
        "event_type": "SALE",
        "quantity": -15,
        "event_id": "evt-2"
    }
]
```

---

## Database Schema

### Tables

#### products

| Column | Type | Constraints |
|--------|------|-------------|
| id | SERIAL | PRIMARY KEY |
| name | VARCHAR | NOT NULL |
| sku | VARCHAR | UNIQUE, INDEX |
| created_at | TIMESTAMP | DEFAULT now() |

#### inventory_events

| Column | Type | Constraints |
|--------|------|-------------|
| id | SERIAL | PRIMARY KEY |
| event_id | VARCHAR | UNIQUE, NOT NULL |
| product_id | INTEGER | FOREIGN KEY → products.id, NOT NULL |
| event_type | ENUM | NOT NULL |
| quantity | INTEGER | |
| created_at | TIMESTAMP | DEFAULT now() |

**Indexes**:
- `ix_inventory_events_product_id`
- `ix_inventory_events_created_at`
- `ix_inventory_events_product_created` (composite)

#### inventory_state

| Column | Type | Constraints |
|--------|------|-------------|
| product_id | INTEGER | PRIMARY KEY, FOREIGN KEY → products.id |
| quantity | INTEGER | NOT NULL, DEFAULT 0 |

---

## Event Types

| Event | Effect on Inventory | Notes |
|-------|---------------------|-------|
| `PURCHASE` | +quantity | Stock received from supplier |
| `SALE` | -quantity | Protects against overselling |
| `DAMAGE` | -quantity | Stock damaged/lost |
| `RETURN` | +quantity | Customer returns |
| `ADJUSTMENT` | ±quantity | Manual correction (can be positive or negative) |

### Quantity Rules

| Event Type | Quantity Must Be | Notes |
|------------|------------------|-------|
| PURCHASE | > 0 | Increases inventory |
| SALE | > 0 | Decreases inventory, checks availability |
| DAMAGE | > 0 | Decreases inventory, checks availability |
| RETURN | > 0 | Increases inventory |
| ADJUSTMENT | any non-zero | Manual correction |

---

## Testing

### Run All Tests

```bash
make test
```

Or directly:

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=app tests/
```

### End-to-End Tests (Docker)

```bash
make test-e2e
```

### Run All Tests (Unit + E2E)

```bash
make test-all
```

### Test Structure

| File | Description |
|------|-------------|
| `test_products.py` | Product creation and SKU uniqueness |
| `test_inventory.py` | Core inventory flow, oversell protection |
| `test_inventory_validation.py` | Input validation for event types |
| `test_idempotency.py` | Duplicate event handling |
| `conftest.py` | Shared pytest fixtures (TestClient, database) |

---

## Development Workflow

### Making Schema Changes

1. Modify SQLAlchemy models in `app/models/`
2. Generate a migration:
   ```bash
   alembic revision --autogenerate -m "description"
   ```
3. Review the generated migration file in `migrations/versions/`
4. Apply the migration:
   ```bash
   alembic upgrade head
   ```

### Using Makefile

```bash
make up          # Start services
make logs        # View logs
make test        # Run tests
make migrate     # Apply migrations
make shell       # Shell into container
make reset       # Full reset (destroys data)
make export      
make export      → export events to data lake
make warehouse   → build dim_products and dim_dates (Python)
make dbt-run     → build all dbt models
make dbt-test    → run data quality tests
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/ims` | PostgreSQL connection string |
| `PYTHONPATH` | `/app` | Python module search path |

---

## Roadmap

IMS is developed in epochs, evolving from a simple backend to a full data platform. See [ROADMAP.md](ROADMAP.md) for full details.

| Epoch | Focus | Status |
|-------|-------|--------|
| 0 | Foundations | ✅ Complete |
| 1 | Event-Driven Backend | ✅ Complete |
| 2 | Batch Data Platform | ✅ Complete |
| 3 | Data Warehouse | ✅ Complete |
| 4 | Streaming Platform | ✅ Complete |
| 5 | ML Platform | ✅ Complete |
| 6 | Application Layer | In Progress |
| 7 | Advanced Automation | Optional |

---

## License

MIT License


## Author

**Sinan Demir**   
Computer Science Student @ University of Texas at Dallas