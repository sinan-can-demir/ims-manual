# Data Lake — Inventory Management System (IMS)

## Overview

This directory contains exported datasets derived from the transactional event store.

The data lake is designed to support:
- Analytical queries
- Reproducible data pipelines
- Future machine learning workflows

All datasets are generated from the `inventory_events` table, which serves as the source of truth.

---

## Data Flow

```
PostgreSQL (OLTP)
    ↓
Event Export Script (Python)
    ↓
Parquet Files (Data Lake)
    ↓
Analytics / ML / Warehouse
```

---

## Directory Structure

```
datalake/
  events/
    date=YYYY-MM-DD/
      events.parquet
```

- Data is partitioned by date for efficient querying
- Each file contains a batch of exported events

---

## Dataset: inventory_events

Each record represents a single immutable event.

### Schema

| Column      | Type     | Description                        |
|-------------|----------|------------------------------------|
| event_id    | string   | Unique identifier for idempotency  |
| product_id  | integer  | Product reference                 |
| event_type  | string   | Type of event (purchase, sale, etc.) |
| quantity    | integer  | Quantity change                    |
| version     | integer  | Event schema version               |
| created_at  | datetime | Event creation timestamp           |
| source      | string   | Origin of the event (e.g., API)   |

---

## Export Process

Data is exported from PostgreSQL using a batch script:

```bash
python scripts/export_events.py
```

The export process:
1. Reads events incrementally
2. Writes to partitioned Parquet files
3. Preserves schema consistency

---

## Design Principles

### 1. Immutable Data

Events are append-only and never updated or deleted.

### 2. Reproducibility

All datasets can be rebuilt from the event log.

### 3. Partitioning

Data is partitioned by date to support scalable queries.

### 4. Schema as Contract

The schema is versioned and treated as a stable interface.

---

## Future Improvements

- Incremental exports using checkpoints
- Integration with data warehouse (dbt models)
- Real-time streaming via Kafka
- Feature tables for machine learning

---

## Notes

This data lake is the foundation for:
- Analytics (KPIs, reporting)
- Forecasting models
- Anomaly detection systems
