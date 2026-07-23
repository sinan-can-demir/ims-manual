# IMS Milestone — Epoch 3 — Data Warehouse

## Date: 2026-03-29
## Focus: Build an Analytical Layer on Top of the Data Lake

---

## 🎯 Goal

Introduce a **data warehouse** that transforms raw inventory events into
clean, queryable analytical tables.

This enables:

- Answering business questions with SQL (daily stock levels, turnover rate,
  event counts)
- Building a foundation for ML feature tables in Epoch 5
- Separating analytical concerns from the transactional system

---

## 🧠 Tool Decision: DuckDB

**Chosen approach:** DuckDB as the local analytical engine.

**Why not Postgres analytical schema:**
Postgres is an OLTP database — not optimized for columnar scans or
aggregations over large datasets. It would work but becomes the wrong
tool as data grows.

**Why not dbt yet:**
dbt is the industry standard transformation framework and will be
introduced in Epoch 4. Writing raw SQL first ensures you understand
what the transformations are doing before adding a framework on top.

**Why DuckDB:**
- Embedded, zero infrastructure — just a Python library
- Reads Parquet files natively without loading them into memory first
- Optimized for analytical queries (columnar engine)
- Industry adoption is growing fast — used at many data teams for local dev
- Natural bridge to dbt later

```python
import duckdb

# This single line reads your entire partitioned data lake
duckdb.sql("SELECT * FROM 'data_lake/inventory_events/**/*.parquet'")
```

**Progression:**
```
Epoch 3 — DuckDB + raw SQL transformations
              ↓
Epoch 4 — introduce dbt to organize and test those transformations
              ↓
Epoch 5 — Kafka streaming into the warehouse
```

---

## 🏗️ Target Schema

The warehouse follows a **star schema** — a central fact table surrounded
by dimension tables. This is the standard pattern for analytical systems.

```
dim_products ──────┐
                   ▼
dim_dates ────► fact_inventory_events
```

### fact_inventory_events
The central table. One row per inventory event, enriched with keys to
dimension tables.

| Column | Type | Description |
|---|---|---|
| event_id | VARCHAR | Natural key from source |
| product_id | INTEGER | FK to dim_products |
| date_id | VARCHAR | FK to dim_dates (YYYY-MM-DD) |
| event_type | VARCHAR | PURCHASE, SALE, DAMAGE, etc. |
| quantity | INTEGER | Normalized delta |
| created_at | TIMESTAMP | Original event timestamp |

### dim_products
One row per product. Slowly changing — for now treated as static.

| Column | Type | Description |
|---|---|---|
| product_id | INTEGER | PK |
| name | VARCHAR | Product name |
| sku | VARCHAR | Stock keeping unit |
| created_at | TIMESTAMP | When product was created |

### dim_dates
One row per calendar date. Pre-generated, not derived from events.

| Column | Type | Description |
|---|---|---|
| date_id | VARCHAR | PK — format YYYY-MM-DD |
| year | INTEGER | |
| month | INTEGER | |
| day | INTEGER | |
| quarter | INTEGER | |
| day_of_week | VARCHAR | Monday, Tuesday, etc. |
| is_weekend | BOOLEAN | |

---

## 🏗️ Tasks

---

### BLOCK 1 — Setup (30 min)

- [x] Install DuckDB
  ```bash
  pip install duckdb
  ```
- [x] Add `duckdb` to `requirements.txt`
- [x] Create `warehouse/` directory at project root
- [x] Create `warehouse/README.md` explaining the warehouse structure
- [x] Add `*.duckdb` to `.gitignore` (database files should not be committed)

---

### BLOCK 2 — Dimension Tables (45 min)

**New file:** `app/services/warehouse_service.py`

- [x] Build `dim_products` from PostgreSQL products table
  - Query all products via SQLAlchemy
  - Write to `warehouse/dim_products.parquet`

- [x] Build `dim_dates`
  - Generate a date range (e.g. 2026-01-01 to 2030-12-31)
  - Derive year, month, day, quarter, day_of_week, is_weekend
  - Write to `warehouse/dim_dates.parquet`

- [x] Add a `build_dimensions(db)` function that runs both

**Why pre-generate dim_dates:**
Date dimensions are always pre-generated in real warehouses — you never
derive them from events because you need dates that haven't happened yet
for forecasting and reporting.

**Commit:**
```bash
git commit -m "feat(warehouse): add dimension table builders"
```

---

### BLOCK 3 — Fact Table (1 hour)

**File:** `app/services/warehouse_service.py`

- [x] Read all exported Parquet files from `data_lake/inventory_events/`
  using DuckDB
- [x] Join with `dim_products` on `product_id`
- [x] Join with `dim_dates` on date portion of `created_at`
- [x] Select final fact columns
- [x] Write to `warehouse/fact_inventory_events.parquet`

```python
import duckdb

result = duckdb.sql("""
    SELECT
        e.event_id,
        e.product_id,
        strftime(e.created_at, '%Y-%m-%d') AS date_id,
        e.event_type,
        e.quantity,
        e.created_at
    FROM 'data_lake/inventory_events/**/*.parquet' e
    JOIN 'warehouse/dim_products.parquet' p
        ON e.product_id = p.product_id
""").df()
```

- [x] Add a `build_fact_table()` function
- [x] Add a `build_warehouse(db)` orchestrator that calls dimensions first,
  then fact table

**Commit:**
```bash
git commit -m "feat(warehouse): add fact table builder"
```

---

### BLOCK 4 — Analytical Queries (45 min)

**New file:** `warehouse/queries.sql`

Write and verify these queries against the fact table using DuckDB:

- [x] **Daily inventory delta** — total quantity change per product per day
  ```sql
  SELECT
      date_id,
      product_id,
      SUM(quantity) AS daily_delta
  FROM fact_inventory_events
  GROUP BY date_id, product_id
  ORDER BY date_id, product_id
  ```

- [x] **Event type breakdown** — count of each event type
  ```sql
  SELECT
      event_type,
      COUNT(*) AS event_count,
      SUM(quantity) AS total_quantity
  FROM fact_inventory_events
  GROUP BY event_type
  ```

- [x] **Running inventory balance** — cumulative stock level over time
  ```sql
  SELECT
      product_id,
      date_id,
      SUM(quantity) OVER (
          PARTITION BY product_id
          ORDER BY date_id
      ) AS running_balance
  FROM fact_inventory_events
  ```

**Why these queries matter:**
These three patterns — daily aggregation, categorical breakdown, and
running totals — are the foundation of almost every inventory analytics
dashboard. The running total using a window function is particularly
important for ML feature engineering later.

**Commit:**
```bash
git commit -m "feat(warehouse): add analytical query examples"
```

---

### BLOCK 5 — CLI Script and Makefile (30 min)

**New file:** `app/scripts/build_warehouse.py`

```python
from app.database import SessionLocal
from app.services.warehouse_service import build_warehouse

def main():
    db = SessionLocal()
    try:
        build_warehouse(db)
    finally:
        db.close()

if __name__ == "__main__":
    main()
```

- [x] Create `app/scripts/build_warehouse.py`
- [x] Add Makefile target:
  ```makefile
  warehouse:
      python -m app.scripts.build_warehouse
  ```
- [x] Test end-to-end:
  ```bash
  make export      # export events to parquet first
  make warehouse   # build warehouse from parquet
  ```

**Commit:**
```bash
git commit -m "feat(warehouse): add CLI script and Makefile target"
```

---

### BLOCK 6 — Tests (45 min)

**New file:** `tests/test_warehouse.py`

- [x] Test `dim_dates` covers expected date range and has correct columns
- [x] Test `dim_products` matches products in the database
- [x] Test `fact_inventory_events` row count matches exported events
- [ ] Test running balance query produces correct result for a known sequence
  of events

**Commit:**
```bash
git commit -m "test: add warehouse builder tests"
```

---

### BLOCK 7 — Documentation and Roadmap (15 min)

- [x] Update `warehouse/README.md` with schema, query examples, and
  how to rebuild
- [x] Update `ROADMAP.md` — mark Epoch 3 in progress
- [x] Update `Last Updated` date

**Commit:**
```bash
git commit -m "docs: add warehouse README and update roadmap"
```

---

## 🧪 Definition of Done

Epoch 3 is complete when:

- [x] DuckDB installed and reading Parquet files
- [x] `dim_products`, `dim_dates`, `fact_inventory_events` all building correctly
- [x] Three analytical queries verified and documented
- [x] `make warehouse` runs end-to-end cleanly after `make export`
- [x] Tests passing
- [x] `warehouse/README.md` explains the schema clearly

---

## 📋 Suggested Commit Order

```
feat(warehouse): add dimension table builders
feat(warehouse): add fact table builder
feat(warehouse): add analytical query examples
feat(warehouse): add CLI script and Makefile target
test: add warehouse builder tests
docs: add warehouse README and update roadmap
```

---

## ⚠️ Things to Watch Out For

**Parquet files must exist before building the warehouse.**
Run `make export` first. If the data lake is empty the fact table will
be empty too — this is correct behavior, not a bug.

**DuckDB reads Parquet directly — no loading step.**
You don't insert data into DuckDB tables. You query Parquet files
in place. This is intentional and is one of DuckDB's key advantages.

**dim_dates is static — generate it once.**
You only need to regenerate it if you extend the date range. It does
not depend on your event data.

**The warehouse is a derived artifact.**
Like Parquet exports, the warehouse files should not be committed to git.
They are always rebuildable from source. Add `warehouse/*.parquet` and
`warehouse/*.duckdb` to `.gitignore`.

---

## 🚀 Next Milestone Preview

Once Epoch 3 is complete the system has a full analytical layer.

The next session will begin **Epoch 4**, with two possible directions:

- **dbt** — introduce transformation framework to organize and test
  the SQL models you wrote in Epoch 3
- **Kafka** — introduce real-time streaming as an alternative write path

The recommended order is dbt first — it builds directly on Epoch 3
work and teaches you a tool that appears in almost every modern data
engineering job description.
