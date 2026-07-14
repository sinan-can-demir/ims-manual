> **Archived — superseded.** This was a point-in-time AI code review performed on
> branch `epoch6-application` (2026-06-13). Its "Fixed?" column reads "No" for every
> finding, but most items were subsequently addressed in commit `e1e9ccc` ("fix:
> address code review findings across API, models, tests, and infra") and the
> follow-up API-key authentication work. Kept here as project history, not as a
> current status report — see `ROADMAP.md` and `SECURITY.md` for the current state.

# IMS — Code Review Report

**Reviewer:** Claude Sonnet 4.6  
**Date:** 2026-06-13  
**Branch:** epoch6-application  
**Scope:** All source files — API layer, services, models, tests, migrations, dashboard, scripts  
**Method:** Full file read + manual endpoint probing + coverage analysis + static analysis

---

## Executive Summary

The core of this system — the event-sourced inventory backend — is well-built. The CQRS pattern is applied correctly, transactions are atomic, the idempotency mechanism is real and thoughtful, and the data pipeline architecture (Parquet → DuckDB → dbt → Prophet) is coherent end-to-end.

What this codebase lacks is a **production safety layer**. There is no authentication anywhere. Destructive admin operations are exposed as public HTTP endpoints. Input validation has meaningful gaps. Three tests pass because they silently hit pre-existing files on disk rather than running in isolation.

This is a learning project and those patterns are understandable — but if this were deployed publicly as-is, any person who knows the URL could erase inventory state or trigger an unbounded export.

Test coverage is 76% overall. The gaps are concentrated in exactly the places that matter most: the forecast/restock API, the training pipeline, and the error-handling branches.

---

## Critical

### C1 — No authentication on any endpoint

**Location:** `app/main.py`, all API routers  
**Confirmed by:** Every endpoint called without any credentials — all return data or mutate state freely.

Every endpoint in this system is publicly accessible. There is no API key check, no JWT middleware, no session validation — nothing. This includes the two destructive admin operations below.

For a learning project running locally this is fine. For a public AWS deployment it is unacceptable. Anyone who discovers the domain can create products, record events, trigger exports, and wipe inventory state.

**Fix:** Add a FastAPI dependency that checks an `X-API-Key` header against a value stored in an environment variable. Apply it globally via `app.dependency_overrides` or per-router via `dependencies=[Depends(require_api_key)]`. This is Phase 2 work already planned.

---

### C2 — POST /api/inventory/replay is a public destructive operation

**Location:** `app/api/inventory.py:32`, `app/services/replay_service.py:24`  
**Confirmed by:** `POST /api/inventory/replay` called without credentials — returns 200 and reports 0 events processed.

The replay endpoint deletes every row in `inventory_state` and rebuilds from scratch. Here is the exact code path:

```python
# replay_service.py:24
db.query(InventoryState).delete()
```

This `DELETE` is inside the same transaction as the rebuild, which is correct. However: there is no exclusive lock on the table, no auth, and no confirmation step. A live production system receiving concurrent event writes while replay runs has an undefined outcome — `SELECT FOR UPDATE` in `inventory_service.py` locks individual rows but does not prevent the `DELETE` from completing.

This endpoint exists for debugging/admin use. It must not be reachable without auth, and in production it should require an explicit flag or be removed from the HTTP API entirely and demoted to a CLI script.

**Fix:** In the short term, protect with the API key middleware. Long term, remove from the HTTP API and make it an `alembic`-style CLI command.

---

### C3 — Raw exception text sent to clients

**Location:** `app/api/forecast.py:24`, `app/api/forecast.py:53`

```python
# forecast.py:24
raise HTTPException(status_code=500, detail=str(e))

# forecast.py:53
raise HTTPException(status_code=500, detail=str(e))
```

`str(e)` on an unhandled exception exposes the full internal error message to the client — file paths, library internals, stack frames in some cases. This leaks information about your server's directory structure and internal state. An interviewer or security reviewer will flag this immediately.

**Fix:**
```python
raise HTTPException(status_code=500, detail="Internal server error")
```
Log the actual exception at `logger.exception(...)` before raising.

---

## High

### H1 — GET /api/inventory/{product_id} returns 200 for nonexistent products

**Location:** `app/services/inventory_service.py:38-44`, `app/api/inventory.py:37-41`  
**Confirmed by:** `GET /api/inventory/9999` returns `{"product_id": 9999, "quantity": 0}` — a product that does not exist.

```python
def get_inventory(db: Session, product_id: int) -> int:
    state = db.query(InventoryState).filter(...).first()
    return state.quantity if state else 0   # <-- silently returns 0
```

This is a misleading return value. A caller cannot distinguish between "this product has zero inventory" and "this product does not exist." It also creates a subtle data integrity risk: if a client polls inventory for a product they created moments ago (before the first event), they see 0, which is technically correct — but for a product that was never created they also see 0, which is wrong.

The API contract should be 404 for nonexistent products and 200 with `quantity: 0` only when the product exists but has no events.

**Fix:**
```python
def get_inventory(db: Session, product_id: int) -> int:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    state = db.query(InventoryState).filter(...).first()
    return state.quantity if state else 0
```

---

### H2 — No input length constraints on any string field

**Location:** `app/schemas/product.py:6-7`, `app/schemas/inventory_event.py:10-13`  
**Confirmed by:** A 5,000-character SKU and an empty string SKU both return 201.

```
5000-char SKU accepted: 201
Empty SKU accepted: 201
```

`product.name`, `product.sku`, and `inventory_event.event_id` are plain `str` with no `min_length` or `max_length`. The database columns are `VARCHAR` with no length limit either. This means:

- A client can write a multi-megabyte `event_id` to every event, bloating the table
- An empty string `""` is a valid SKU — the unique constraint then makes `""` a reserved SKU
- An empty `event_id` goes through the full idempotency check and then fails on the product lookup (because the product also doesn't exist in the test environment) — but with a real product, an empty `event_id` would be stored and all subsequent empty-id events would be treated as duplicates

**Fix (Pydantic):**
```python
from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    sku: str = Field(min_length=1, max_length=100)

class InventoryEventCreate(BaseModel):
    event_id: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ne=0)  # also enforces non-zero at schema level
```

---

### H3 — InventoryEvent.quantity is nullable at the database level

**Location:** `app/models/inventory_event.py:32`, `migrations/versions/d6e00aa295e6_initial_schema.py:38`

```python
quantity = Column(Integer)   # no nullable=False
```

The migration reflects this: the column is created as nullable. A `None` quantity would pass Pydantic validation (since `int` in Pydantic does not accept None by default, so this is only reachable via a raw DB insert) but would crash the inventory calculation at `state.quantity + delta` with a `TypeError`.

This is a belt-and-suspenders issue — the Pydantic schema guards against None from the API — but a schema that can store invalid data is a time bomb for direct DB access, migrations, or backfill scripts.

**Fix:** Add `nullable=False` to the column and generate a migration:
```python
quantity = Column(Integer, nullable=False)
```

---

### H4 — Two tests depend on real files on disk and have no isolation

**Location:** `tests/test_forecast.py:85-91`

```python
def test_feature_columns():
    df = pd.read_parquet("feature_store/daily_sales.parquet")  # hits real disk
    ...

def test_forecast_returns_n_days():
    df = forecast(8, days=7)   # loads real model for product_id=8 from models/
    assert len(df) == 7
```

These two tests silently depend on:
1. `feature_store/daily_sales.parquet` existing at the correct relative path
2. A trained Prophet model for product_id=8 existing in `models/`

They pass in your environment because you've run `make features` and `make train`. In a clean checkout, a fresh Docker container, or a CI runner, they will fail with `FileNotFoundError`. This gives the test suite a false green.

They are also not isolated — they share state with production data. Running the tests mutates nothing, but a bug in `forecast()` would corrupt the test output if models were not read-only.

**Fix:** Mock the file I/O with `tmp_path` fixtures, or use `@pytest.mark.skipif` with a check for the file's existence and document why. At minimum, these should be moved to a separate integration test file that is explicitly excluded from the default test run.

---

### H5 — Tests use SQLite, not PostgreSQL — concurrency guarantees are untested

**Location:** `tests/conftest.py:14-18`

The concurrency-critical path — `SELECT FOR UPDATE` in `inventory_service.py:80` — is silently ignored by SQLite. SQLite has no row-level locking and no support for `FOR UPDATE`. The ORM emits the clause, SQLite ignores it, and the test passes because no concurrent access is happening anyway.

The result: you have zero test coverage of the actual production behavior under concurrent writes. The oversell protection relies on `SELECT FOR UPDATE` working correctly. In PostgreSQL it does. In the test suite, it is never tested.

**Fix (Phase 4 in the roadmap):** Run integration tests against a real Postgres instance. The standard pattern is a Docker-in-Docker Postgres service in CI, or a `pytest-postgresql` fixture locally. This is the most impactful testing gap in the project.

---

## Medium

### M1 — GET /api/forecast/restock/{product_id} silently accepts nonexistent products

**Location:** `app/services/restock_service.py:7-50`, `app/api/forecast.py:42-56`

`get_restock_recommendation()` calls `get_inventory(db, product_id)` which returns 0 for any product that doesn't exist (see H1). It then calls `forecast(product_id, days=7)` which raises `FileNotFoundError` if no model is trained — this is correctly surfaced as a 404. But if a model exists for product_id=8 and a caller requests `/api/forecast/restock/99999`, they get back a legitimate-looking restock recommendation for a nonexistent product with 0 inventory.

**Fix:** Validate product existence before proceeding in `get_restock_recommendation` or in the endpoint.

---

### M2 — warehouse_service.build_warehouse() swallows exceptions silently

**Location:** `app/services/warehouse_service.py:103-124`

```python
def build_warehouse(...) -> bool:
    try:
        ...
        return True
    except Exception as e:
        print(f"Warehouse build failed: {e}")   # goes nowhere in production
        return False
```

This function returns `False` on failure and prints to stdout. In a container, stdout may be captured but the calling script has no way to distinguish success from failure without checking the return value. The calling script (`app/scripts/build_warehouse.py`) does not check the return value at all.

If the warehouse build fails silently, downstream pipelines (dbt, feature engineering, model training) will run on stale or missing data without any indication of the upstream failure.

**Fix:** Remove the try/except entirely. Let exceptions propagate. The CLI script can catch them at the top level if it needs a non-zero exit code.

---

### M3 — f-string SQL with path interpolation in DuckDB queries

**Location:** `app/services/warehouse_service.py:80-91`

```python
result = conn.execute(f"""
    SELECT ...
    FROM read_parquet('{INVENTORY_EVENTS_ROOT}/**/*.parquet') e
    JOIN read_parquet('{WAREHOUSE_ROOT}/dim_products.parquet') p
    ...
""")
```

`INVENTORY_EVENTS_ROOT` and `WAREHOUSE_ROOT` come from environment variables via `app/config.py`. These are not user-controlled in the current architecture, but using f-strings to interpolate values into SQL is a habit that will eventually cause a bug. If `DATA_LAKE_ROOT` were ever read from an HTTP request parameter or a config file with insufficient validation, this becomes a path injection.

The correct pattern for DuckDB is parameterized queries where the driver supports it, or explicit validation of path values before interpolation.

**Fix:** At minimum, validate that the paths are absolute and don't contain shell metacharacters before interpolating. Ideally, use DuckDB's parameter binding for literal values.

---

### M4 — Route ordering: /{product_id} defined before /events/{product_id}

**Location:** `app/api/inventory.py:36-58`

```python
@router.get("/{product_id}", ...)      # line 36
def inventory_level(...):

@router.get("/events/{product_id}", ...)  # line 44
def get_product_events(...):
```

FastAPI's type validation (product_id is `int`) prevents a literal conflict here — "events" cannot be parsed as an integer so the first route does not shadow the second. However, defining a catch-all path parameter before a specific static segment is fragile. In Express or Flask, this ordering would break. Anyone maintaining this code who adds a new route between these two needs to understand the implicit dependency on type coercion.

Convention in FastAPI: always define specific paths before dynamic ones.

**Fix:** Reorder — put `/events/{product_id}` before `/{product_id}`.

---

### M5 — print() in test and service code

**Location:** `tests/test_products.py:10-11`, `app/services/warehouse_service.py:113-116`

```python
# test_products.py
print("STATUS:", response.status_code)
print("BODY:", response.json())

# warehouse_service.py
print(f"dim_products: {products_count} rows")
print(f"dim_dates: {dates_count} rows")
print(f"fact_inventory_events: {facts_count} rows")
print(f"Warehouse build failed: {e}")
```

Debug prints left in test code are a red flag for reviewers. In services, `print()` should be replaced with the structured logger — stdout prints are swallowed by container orchestrators that expect JSON-formatted log lines, not raw strings mixed into the log stream.

**Fix:** Remove the prints from the test. Replace service prints with `logger.info(...)` and `logger.exception(...)`.

---

## Low

### L1 — forecast.py API coverage is 58%

**Location:** `app/api/forecast.py` — lines 23-36, 48-57 not covered

The happy path of both forecast endpoints (`GET /api/forecast/{product_id}` and `GET /api/forecast/restock/{product_id}`) has no test coverage. Only the 404 path (no trained model) is tested. This means the response serialization, the `ForecastPoint` construction loop, and the `RestockResponse` mapping are all untested.

If the schema changes (e.g., adding a field to `RestockResponse`), the tests will not catch a serialization failure.

---

### L2 — InventoryState.quantity uses Python-side default, not server_default

**Location:** `app/models/inventory_state.py:27-30`

```python
quantity = Column(Integer, nullable=False, default=0)
```

`default=0` is a SQLAlchemy client-side default — it applies when inserting via the ORM. A raw `INSERT INTO inventory_state (product_id) VALUES (1)` executed directly against the database or in a migration script would fail because the column has no `server_default` and is `NOT NULL`.

**Fix:**
```python
quantity = Column(Integer, nullable=False, server_default="0")
```

---

### L3 — Dashboard reads from a hardcoded relative path

**Location:** `dashboard/app.py:99`

```python
feature_df = pd.read_parquet("feature_store/daily_sales.parquet")
```

This path is relative to the working directory when `streamlit run` is invoked. If the dashboard is started from any directory other than the project root, it crashes with `FileNotFoundError`. In AWS (ECS container, different working directory), this will fail unless the Dockerfile explicitly sets `WORKDIR` to the right path and the file is present.

**Fix:** Use `Path(__file__).resolve().parent.parent / "feature_store" / "daily_sales.parquet"` — this is the same pattern used in `app/config.py` and already works correctly there.

---

### L4 — Dockerfile has no HEALTHCHECK instruction

**Location:** `docker/Dockerfile`

AWS ECS can use either a load balancer health check or a container-level HEALTHCHECK. The Dockerfile currently has neither. Adding one is cheap and provides an additional safety net when the load balancer health check is misconfigured.

**Fix:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

---

### L5 — No test for the idempotency duplicate status code contract

**Location:** `tests/test_idempotency.py`

The idempotency test verifies that duplicate events don't double-count inventory — which is correct. But it does not verify the status code returned for a duplicate. The service returns the existing event on duplicate, which the API layer returns as 201. Whether a duplicate should return 200 or 201 is a deliberate API design choice (200 = idempotent replay, 201 = created). The test is silent on this.

**Fix:** Add `assert response.status_code == 200` (or 201 — pick one and enforce it) for the duplicate request.

---

## Summary Table

| ID | Severity | File | Issue | Fixed? |
|----|----------|------|-------|--------|
| C1 | Critical | all routers | No authentication on any endpoint | No |
| C2 | Critical | `api/inventory.py:32` | POST /replay is public and destructive | No |
| C3 | Critical | `api/forecast.py:24,53` | Raw exception text sent to clients | No |
| H1 | High | `services/inventory_service.py:44` | GET /inventory/{id} returns 200 for nonexistent products | No |
| H2 | High | `schemas/product.py`, `schemas/inventory_event.py` | No length constraints on any string field | No |
| H3 | High | `models/inventory_event.py:32` | quantity column is nullable in DB | No |
| H4 | High | `tests/test_forecast.py:85-91` | Two tests depend on real files on disk | No |
| H5 | High | `tests/conftest.py:14` | Tests use SQLite — SELECT FOR UPDATE untested | No |
| M1 | Medium | `services/restock_service.py` | Restock accepts nonexistent product IDs | No |
| M2 | Medium | `services/warehouse_service.py:103` | build_warehouse() swallows exceptions | No |
| M3 | Medium | `services/warehouse_service.py:80` | f-string SQL with path interpolation | No |
| M4 | Medium | `api/inventory.py:36-44` | Route order: dynamic before specific | No |
| M5 | Medium | `test_products.py:10`, `warehouse_service.py:113` | print() in test and service code | No |
| L1 | Low | `api/forecast.py` | 58% coverage — happy paths untested | No |
| L2 | Low | `models/inventory_state.py:27` | Python-side default, not server_default | No |
| L3 | Low | `dashboard/app.py:99` | Hardcoded relative path for feature store | No |
| L4 | Low | `docker/Dockerfile` | No HEALTHCHECK instruction | No |
| L5 | Low | `tests/test_idempotency.py` | Duplicate event status code not asserted | No |

---

## Suggested Fix Order

Fix the Criticals before any public deployment. The Highs before production traffic. The Mediums before the next engineer reads this code.

1. **C1** — Add API key auth (FastAPI dependency, one file, ~30 lines)
2. **C2** — Restrict replay endpoint behind auth; add CLI alternative
3. **C3** — Replace `str(e)` with generic message + `logger.exception()`
4. **H1** — Add 404 for nonexistent product in `get_inventory`
5. **H2** — Add `Field(min_length, max_length)` to all string schemas
6. **H3** — Add `nullable=False` to `quantity` column, generate migration
7. **M5** — Remove prints, replace with logger
8. **M2** — Remove try/except from `build_warehouse`, let it raise
9. **M4** — Reorder routes
10. **H4** — Isolate the two disk-dependent tests
11. **L3** — Fix dashboard path
12. **L4** — Add Dockerfile HEALTHCHECK
13. **L2** — Add `server_default` to `inventory_state.quantity`
14. **H5** — Postgres-backed integration tests (Phase 4)
15. **M1** — Validate product existence in restock endpoint
16. **L1** — Add forecast happy-path tests
17. **L5** — Assert idempotency status code
18. **M3** — Validate paths before DuckDB interpolation
