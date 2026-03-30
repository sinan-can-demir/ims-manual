# IMS Milestone — Epoch 4 — dbt Transformations

## Date: 2026-03-29
## Focus: Replace Python Warehouse Service with dbt Models

---

## 🎯 Goal

Introduce **dbt (data build tool)** to replace the hand-written Python
warehouse service with properly organized, tested, and documented SQL
transformations.

This enables:

- SQL models that are version controlled and reproducible
- Automatic data quality testing (not null, unique, relationships)
- Auto-generated documentation for every model and column
- Industry-standard transformation workflow used at most data teams

---

## 🧠 Why dbt — and Why Now

You already built the warehouse manually in Epoch 3. You understand:
- What dim_products, dim_dates, and fact_inventory_events contain
- How DuckDB reads Parquet files
- Why star schema separates facts from dimensions
- What the SQL transformations actually do

dbt doesn't change any of that. It just organizes your SQL into a
proper project structure, runs it in dependency order, and adds
testing and documentation on top.

**The mental model:**

```
Epoch 3 — you wrote the SQL and understood it
Epoch 4 — dbt organizes, tests, and documents that same SQL
```

Nothing you built is wasted. The concepts transfer directly.

---

## 🧠 How dbt Works

dbt has a simple mental model:

```
sources  →  staging models  →  mart models
  ↑               ↑                ↑
raw data      light cleanup    business logic
(Parquet)    (rename, cast)   (joins, aggregates)
```

For IMS specifically:

```
data_lake/inventory_events/  →  stg_inventory_events  →  fact_inventory_events
warehouse/dim_products.parquet  →  (already clean)    →  dim_products
                                                        →  dim_dates
```

Each model is just a `.sql` file with a SELECT statement. dbt handles
running them in the right order based on dependencies.

---

## 🛠️ Tool Decision: dbt-duckdb

dbt has adapters for different databases. Since you're using DuckDB
as your analytical engine, you'll use `dbt-duckdb`.

```bash
pip install dbt-duckdb
```

This is the only new dependency. No new infrastructure needed.

---

## 🏗️ Tasks

---

### BLOCK 1 — Setup (45 min)

- [x] Install dbt-duckdb
  ```bash
  pip install dbt-duckdb
  ```
- [x] Add `dbt-duckdb` to `requirements.txt` ## requires python 11
- [x] Initialize dbt project inside `warehouse/`:
  ```bash
  cd warehouse
  dbt init ims_warehouse
  ```
- [x] Configure `profiles.yml` to use DuckDB with your Parquet files
- [x] Configure `dbt_project.yml` with project name and model paths
- [x] Add `warehouse/ims_warehouse/target/` to `.gitignore`
  - dbt writes compiled SQL and run artifacts here — never commit them
- [x] Run `dbt debug` to verify connection works

**What `profiles.yml` looks like for dbt-duckdb:**
```yaml
ims_warehouse:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "warehouse/ims.duckdb"
      threads: 4
```

**Commit:**
```bash
git commit -m "chore(dbt): initialize dbt project with duckdb adapter"
```

---

### BLOCK 2 — Sources (30 min)

In dbt, **sources** declare where your raw data comes from.
For IMS, your sources are the Parquet files in the data lake.

**New file:** `warehouse/ims_warehouse/models/sources.yml`

```yaml
version: 2

sources:
  - name: data_lake
    description: "Partitioned Parquet files exported from PostgreSQL"
    tables:
      - name: inventory_events
        description: "Append-only inventory event log"
        columns:
          - name: event_id
            description: "Unique event identifier"
          - name: product_id
            description: "FK to products"
          - name: event_type
            description: "PURCHASE, SALE, DAMAGE, ADJUSTMENT, RETURN"
          - name: quantity
            description: "Normalized quantity delta"
          - name: created_at
            description: "Event timestamp"
```

- [x] Create `sources.yml` declaring inventory_events as a source
- [x] Verify dbt can read the source with `dbt source freshness`

**Commit:**
```bash
git commit -m "feat(dbt): add data lake sources declaration"
```

---

### BLOCK 3 — Staging Model (30 min)

Staging models do light cleanup on raw sources — renaming columns,
casting types, adding derived fields. No business logic yet.

**New file:** `warehouse/ims_warehouse/models/staging/stg_inventory_events.sql`

```sql
-- Staging model for inventory events
-- Reads from partitioned Parquet data lake
-- Adds date_id derived from created_at for joining to dim_dates

SELECT
    event_id,
    product_id,
    event_type,
    quantity,
    created_at,
    strftime(created_at, '%Y-%m-%d') AS date_id
FROM {{ source('data_lake', 'inventory_events') }}
```

The `{{ source(...) }}` syntax is dbt's way of referencing sources.
dbt resolves this to the actual Parquet path at runtime.

- [x] Create `models/staging/` directory
- [x] Write `stg_inventory_events.sql`
- [x] Run `dbt run --select stg_inventory_events` and verify output
- [x] Add model description to `schema.yml`

**Commit:**
```bash
git commit -m "feat(dbt): add staging model for inventory events"
```

---

### BLOCK 4 — Dimension Models (45 min)

Convert your existing dimension logic into dbt models.

**New files:**
- `warehouse/ims_warehouse/models/marts/dim_products.sql`
- `warehouse/ims_warehouse/models/marts/dim_dates.sql`

`dim_products.sql`:
```sql
-- Product dimension table
-- Source: dim_products.parquet built from PostgreSQL

SELECT
    product_id,
    name,
    sku,
    created_at
FROM read_parquet('{{ env_var("WAREHOUSE_ROOT") }}/dim_products.parquet')
```

`dim_dates.sql` — for now, read from the pre-generated Parquet:
```sql
SELECT
    date_id,
    year,
    month,
    day,
    quarter,
    day_of_week,
    is_weekend
FROM read_parquet('{{ env_var("WAREHOUSE_ROOT") }}/dim_dates.parquet')
```

- [x] Create `models/marts/` directory
- [x] Write `dim_products.sql`
- [x] Write `dim_dates.sql`
- [x] Run `dbt run --select dim_products dim_dates`
- [x] Add descriptions to `schema.yml`

**Commit:**
```bash
git commit -m "feat(dbt): add dimension models for products and dates"
```

---

### BLOCK 5 — Fact Model (45 min)

The central transformation — joins staging events with dimensions.

**New file:** `warehouse/ims_warehouse/models/marts/fact_inventory_events.sql`

```sql
-- Fact table: one row per inventory event
-- Joins events with product and date dimensions

SELECT
    e.event_id,
    e.product_id,
    e.date_id,
    e.event_type,
    e.quantity,
    e.created_at
FROM {{ ref('stg_inventory_events') }} e
JOIN {{ ref('dim_products') }} p
    ON e.product_id = p.product_id
```

The `{{ ref(...) }}` syntax references other dbt models.
dbt automatically runs dependencies in the correct order —
`stg_inventory_events` and `dim_products` will always run before
`fact_inventory_events`.

- [x] Write `fact_inventory_events.sql`
- [x] Run `dbt run` to build all models
- [x] Verify output matches Epoch 3 warehouse output
- [x] Add descriptions to `schema.yml`

**Commit:**
```bash
git commit -m "feat(dbt): add fact_inventory_events model"
```

---

### BLOCK 6 — dbt Tests (45 min)

dbt has built-in generic tests you declare in `schema.yml`:

```yaml
models:
  - name: fact_inventory_events
    columns:
      - name: event_id
        tests:
          - unique
          - not_null
      - name: product_id
        tests:
          - not_null
          - relationships:
              to: ref('dim_products')
              field: product_id
      - name: quantity
        tests:
          - not_null
```

- [x] Add `unique` and `not_null` tests to `fact_inventory_events`
- [x] Add `not_null` tests to `dim_products` and `dim_dates`
- [x] Add `relationships` test linking fact to dim_products
- [x] Run `dbt test` and verify all tests pass
- [x] Fix any failures

**Why dbt tests matter:**
These run every time you build the warehouse. If a bad export
produces null event_ids or duplicate rows, `dbt test` catches it
before the data reaches analysts or ML models.

**Commit:**
```bash
git commit -m "feat(dbt): add schema tests for warehouse models"
```

---

### BLOCK 7 — Documentation (30 min)

dbt auto-generates a documentation website from your `schema.yml`
descriptions.

```bash
dbt docs generate
dbt docs serve
```

This opens a browser with:
- Interactive lineage graph showing model dependencies
- Column-level descriptions for every model
- Test coverage per model

- [x] Add descriptions to every model in `schema.yml`
- [x] Add descriptions to every column
- [x] Run `dbt docs generate` successfully
- [x] Screenshot the lineage graph for your README

**Commit:**
```bash
git commit -m "docs(dbt): add model and column descriptions"
```

---

### BLOCK 8 — Makefile and Cleanup (30 min)

- [x] Add Makefile targets:
  ```makefile
  dbt-run:
      cd warehouse/ims_warehouse && dbt run

  dbt-test:
      cd warehouse/ims_warehouse && dbt test

  dbt-docs:
      cd warehouse/ims_warehouse && dbt docs generate && dbt docs serve
  ```

- [x] Update full pipeline in README:
  ```
  make export      → export events to data lake
  make warehouse   → build dim_products and dim_dates (Python)
  make dbt-run     → build all dbt models
  make dbt-test    → run data quality tests
  ```

- [x] Deprecate `warehouse_service.py` — add a comment at the top:
  ```python
  # NOTE: dim_products and dim_dates builders are kept for bootstrapping.
  # fact_inventory_events is now managed by dbt.
  # See warehouse/ims_warehouse/ for the dbt project.
  ```

- [x] Update ROADMAP.md

**Commit:**
```bash
git commit -m "chore: add dbt Makefile targets and deprecate warehouse service"
```

---

## 🧪 Definition of Done

Epoch 4 is complete when:

- [x] `dbt run` builds all models successfully
- [x] `dbt test` passes all schema tests
- [x] `dbt docs generate` produces documentation
- [x] Lineage graph shows correct model dependencies
- [x] `make dbt-run` works from project root
- [x] fact_inventory_events output matches Epoch 3 output

---

## 📋 Suggested Commit Order

```
chore(dbt): initialize dbt project with duckdb adapter
feat(dbt): add data lake sources declaration
feat(dbt): add staging model for inventory events
feat(dbt): add dimension models for products and dates
feat(dbt): add fact_inventory_events model
feat(dbt): add schema tests for warehouse models
docs(dbt): add model and column descriptions
chore: add dbt Makefile targets and deprecate warehouse service
```

---

## ⚠️ Things to Watch Out For

**`profiles.yml` location:**
dbt looks for `profiles.yml` in `~/.dbt/` by default, not in your
project directory. You can override this with:
```bash
dbt run --profiles-dir .
```
Or set `DBT_PROFILES_DIR` environment variable. Keep `profiles.yml`
in the project for portability but add it to `.gitignore` if it
contains credentials.

**dbt model materialization:**
By default dbt creates views, not tables. For your warehouse you want
tables. Set this in `dbt_project.yml`:
```yaml
models:
  ims_warehouse:
    marts:
      +materialized: table
    staging:
      +materialized: view
```

**Running order matters:**
dbt resolves this automatically via `{{ ref() }}` — but you need to
use `ref()` correctly. If you hardcode a table name instead of using
`ref()`, dbt won't know about the dependency.

---

## 🚀 Next Milestone Preview

Once Epoch 4 is complete you have a fully documented, tested,
reproducible data warehouse.

Epoch 5 has two directions:

- **Kafka** — real-time streaming as an alternative write path
- **ML Platform** — feature tables and demand forecasting

The recommended order depends on your goal:
- Aiming for **data engineering roles** → Kafka next
- Aiming for **ML engineering roles** → ML Platform next
