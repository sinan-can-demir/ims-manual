# IMS — Epoch 2 Development Checklist

## Goal

Turn your event system into a reproducible, scalable data pipeline

---

## EPIC 1 — Data Lake Foundation

### Structure

- [X] Create `data_lake/` directory
- [X] Create `inventory_events/` subfolder
- [X] Ensure `.gitignore` excludes parquet files
- [X] Add README for data_lake structure

### Expected Structure

```
data_lake/
  inventory_events/
    year=YYYY/
      month=MM/
        day=DD/
```

---

## EPIC 2 — Event Export (Batch)

### Core Export

- [X] Create `export_service.py`
- [X] Query events ordered by `(created_at, id)`
- [X] Convert to pandas DataFrame
- [X] Write `.parquet` file

### Partitioning

- [x] Extract year, month, day
- [x] Group by partitions
- [x] Write partitioned files
- [x] Ensure directory auto-creation

### API Access (temporary)

- [x] Add `/inventory/export` endpoint
- [x] Return export metadata (rows, partitions)

### Validation

- [x] Manually create events
- [x] Run export endpoint
- [x] Verify file structure with `tree`
- [x] Load parquet with pandas and inspect

---

## EPIC 3 — Incremental Pipeline

### Concept

Export only new events, not everything.

### Implementation

- [x] Add `last_id` tracking (uses id instead of timestamp — more robust)
- [x] Filter query: `id > last_id`
- [x] Store checkpoint locally (file or table)
- [x] Update checkpoint after export

### New File

- `data_lake/checkpoints.json`

### Behavior

- First run → full export
- Next runs → incremental only
- No duplicate writes

---

## EPIC 4 — Reproducibility

### Goal

Pipeline should be repeatable and deterministic.

### Tasks

- [x] Add CLI script: `python scripts/export_events.py`
- [x] Ensure same input → same output
- [x] Add logging to export process
- [x] Handle empty export gracefully

---

## EPIC 5 — Data Validation

### Goal

Ensure exported data is correct.

### Tasks

- [x] Verify row counts match DB
- [x] Validate schema consistency
- [x] Ensure no duplicate `event_id`
- [x] Add simple validation script

---

## EPIC 6 — Testing (Lightweight)

Optional but strong.

- [x] Test export creates files
- [x] Test partition structure
- [x] Test incremental logic
- [x] Test idempotent export (partial)

---

## EPIC 7 — Logging & Observability

### Extend your logger

- [x] Log export start
- [ ] Log export completion
- [ ] Log number of rows exported
- [ ] Log partition counts

---

## EPIC 8 — Performance Basics

Not optimization, just awareness.

- [x] Avoid loading unnecessary columns
- [ ] Ensure batch export is efficient
- [ ] Keep memory usage reasonable

---

## Milestone Definition (Epoch 2 COMPLETE)

You are done when:

- [x] Events exported to Parquet
- [x] Partitioned by date
- [x] Incremental export working
- [x] Pipeline reproducible
- [x] Data validated

---

## Mental Model Shift

You are now building:

```
Database → Data Lake → Pipelines
```

NOT:

```
API → Response
```

---

## Recommended Order

Do NOT jump around — follow this:

1. Partitioned export
2. Incremental export
3. CLI pipeline
4. Validation
5. Logging improvements

---

## What Comes After This

Once this checklist is done, you move to:

### Epoch 3 — Data Warehouse (dbt, star schema)
