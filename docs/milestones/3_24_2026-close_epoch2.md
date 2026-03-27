# IMS Milestone — 03/24/2026

## Focus: Close Epoch 2 — Bug Fixes, Export Tests, Logging, Pagination

---

## 🎯 Goal

Finish the remaining work needed to officially close **Epoch 1** and **Epoch 2**.

No new features today. The objective is correctness, test coverage, and polish
on what already exists — turning working code into production-quality code.

---

## 🧠 Context

Epoch 1 is functionally complete but has two open items: pagination on the
events listing endpoint, and JSON-format structured logging.

Epoch 2 has the infrastructure and service code in place, but the export
pipeline has zero test coverage. A pipeline with no tests is not done.
Today closes that gap.

There is also a silent Pydantic bug in two schema files that needs to be
fixed before anything else.

---

## ⚠️ Known Issues to Fix First

### Pydantic `model_config` Placement Bug

**Files affected:** `app/schemas/product.py`, `app/schemas/inventory_state.py`

`model_config = ConfigDict(from_attributes=True)` is defined at **module level**
instead of **inside the class body**. This means Pydantic ignores it entirely.

**Why it matters:** SQLAlchemy ORM objects will fail to serialize correctly in
edge cases. It works now by coincidence — not by design.

**Fix:**

```python
# ❌ WRONG — module level, Pydantic ignores this
model_config = ConfigDict(from_attributes=True)

class ProductResponse(BaseModel):
    id: int
    ...

# ✅ CORRECT — inside the class
class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ...
```

Apply this fix to `ProductResponse` and `InventoryStateResponse`.
Run `pytest` after to confirm nothing breaks.

---

## 🏗️ Tasks

---

### BLOCK 1 — Bug Fix (30 min)

- [X] Fix `model_config` placement in `app/schemas/product.py`
- [X] Fix `model_config` placement in `app/schemas/inventory_state.py`
- [X] Run `pytest` — all tests must still pass

**Commit:**
```bash
git commit -m "fix: move model_config inside Pydantic class bodies"
```

---

### BLOCK 2 — Export Service Tests (2–3 hours)

**New file:** `tests/test_export.py`

This is the main work of the day. The export service has meaningful logic —
incremental checkpoints, partitioned parquet writes, schema validation — and
none of it is tested.

#### Known challenge: SQLite datetime issue

The export service calls `pd.to_datetime(df["created_at"], utc=True)`.
SQLite returns naive datetimes (no timezone info), which will cause this to fail
in the test environment. You will need to handle this inside `_rows_to_dataframe`:

```python
# Handle both timezone-aware (Postgres) and naive (SQLite in tests)
df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
# If already tz-naive, localize first:
if df["created_at"].dt.tz is None:
    df["created_at"] = df["created_at"].dt.tz_localize("UTC")
```

Fixing this in the service is the right approach — not in the tests.

#### Tests to write:

- [ ] **Full export creates files**
  - Create a product, add 2 events, call `export_inventory_events(db, incremental=False)`
  - Assert parquet files exist in `data_lake/inventory_events/`
  - Assert returned metadata: `rows_exported == 2`, `files_written >= 1`

- [X] **Partition structure is correct**
  - After export, assert directory structure contains `year=`, `month=`, `day=` folders

- [X] **Schema columns are correct**
  - Load the parquet file with pandas
  - Assert columns match: `id, event_id, product_id, event_type, quantity, created_at`

- [X] **Incremental export only exports new events**
  - Export once (2 events) → assert checkpoint written
  - Add 1 more event → export again with `incremental=True`
  - Assert second export: `rows_exported == 1`

- [X] **Re-running incremental does not duplicate rows**
  - Export once → export again without new events
  - Assert second export: `rows_exported == 0`, `checkpoint_updated == False`

- [X] **Empty export is handled gracefully**
  - Call export with no events in DB
  - Assert: `rows_exported == 0`, no files written, no crash

#### Fixture note:

The export tests write real files to `data_lake/`. Use a `tmp_path` pytest
fixture or patch `INVENTORY_EVENTS_ROOT` and `CHECKPOINT_FILE` in `app/config.py`
to redirect writes to a temp directory. This keeps the test suite clean.

```python
import pytest
from unittest.mock import patch
from pathlib import Path

@pytest.fixture
def export_paths(tmp_path):
    events_root = tmp_path / "inventory_events"
    checkpoint = tmp_path / "checkpoints.json"
    with patch("app.services.export_service.INVENTORY_EVENTS_ROOT", events_root), \
         patch("app.services.export_service.CHECKPOINT_FILE", checkpoint):
        yield events_root, checkpoint
```

**Commit:**
```bash
git commit -m "test: add export service test suite"
git commit -m "fix: handle tz-naive datetimes from SQLite in export service"
```

---

### BLOCK 3 — JSON Structured Logging (45 min)

**File:** `app/core/logging.py`

Currently the logger emits plain text. The `extra={}` fields passed in service
calls are silently dropped because the formatter doesn't include them.

Replace the plain text formatter with a JSON formatter. In production, this
allows log aggregators (Datadog, CloudWatch, Loki) to index structured fields
like `product_id`, `event_id`, and `event_type` directly.

**Option A — Manual JSON formatter (no new dependencies):**

```python
import json
import logging

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Merge any extra fields passed via extra={}
        for key, value in record.__dict__.items():
            if key not in logging.LogRecord(
                "", 0, "", 0, "", (), None
            ).__dict__ and key != "message":
                log_record[key] = value
        return json.dumps(log_record)
```

**Option B — Use `python-json-logger` (cleaner, industry standard):**

```bash
pip install python-json-logger
```

```python
from pythonjsonlogger import jsonlogger

handler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s"
)
handler.setFormatter(formatter)
```

Add `python-json-logger` to `requirements.txt` if you go with Option B.

- [ ] Implement JSON formatter (Option A or B)
- [ ] Verify `extra={}` fields appear in log output
- [ ] Add `python-json-logger` to `requirements.txt` if used
- [ ] Run the app locally and check log output looks correct

**Commit:**
```bash
git commit -m "feat: switch to JSON structured logging"
```

---

### BLOCK 4 — Pagination on Events Endpoint (30 min)

**File:** `app/api/inventory.py`

Add `limit` and `offset` query parameters to `GET /api/inventory/events/{product_id}`.
This is the last open Epoch 1 item.

```python
from fastapi import Query

@router.get("/events/{product_id}", response_model=list[InventoryEventResponse])
def get_product_events(
    product_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    events = (
        db.query(InventoryEvent)
        .filter(InventoryEvent.product_id == product_id)
        .order_by(InventoryEvent.created_at.asc(), InventoryEvent.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return events
```

**Why these defaults:** `limit=50` is a safe default for most API consumers.
`le=500` prevents accidental full-table scans. `ge=1` prevents a limit of 0
returning nothing silently.

- [ ] Add `limit` and `offset` params to events endpoint
- [ ] Add a test: request with `limit=1` returns only 1 event
- [ ] Add a test: request with `offset=1` skips first event

**Commit:**
```bash
git commit -m "feat: add pagination to events listing endpoint"
```

---

### BLOCK 5 — Update Roadmap (10 min)

- [ ] Mark Epoch 1 as **complete** in `ROADMAP.md`
- [ ] Mark Epoch 2 as **complete** in `ROADMAP.md`
- [ ] Update `Last Updated` date

**Commit:**
```bash
git commit -m "docs: close Epoch 1 and Epoch 2 in roadmap"
```

---

## 🧪 Definition of Done

Epoch 1 is closed when:
- [ ] Pydantic bug fixed
- [ ] JSON logging working with `extra={}` fields visible
- [ ] Pagination on events endpoint with tests

Epoch 2 is closed when:
- [ ] All 6 export tests passing
- [ ] SQLite datetime fix in place
- [ ] `pytest` runs clean with no warnings

---

## 📋 Suggested Commit Order

```
fix: move model_config inside Pydantic class bodies
fix: handle tz-naive datetimes from SQLite in export service
test: add export service test suite
feat: switch to JSON structured logging
feat: add pagination to events listing endpoint
docs: close Epoch 1 and Epoch 2 in roadmap
```

Small, focused commits. One fix or feature per commit.

---

## 🚀 Next Milestone Preview

Once today is done, Epoch 2 is fully closed and the system is clean.

The next session will begin **Epoch 3 — Data Warehouse**, starting with:
- Choosing the warehouse tool (DuckDB recommended for local dev)
- Designing `fact_inventory_events` and `dim_products`
- Writing the first transformation query
