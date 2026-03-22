# IMS — Epoch 2 Development Checklist

## Goal

Turn your event system into a reproducible, scalable data pipeline

---

## EPIC 1 — Data Lake Foundation

### Structure

- [X] Create `data_lake/` directory
- [X] Create `inventory_events/` subfolder
- [X] Ensure `.gitignore` excludes parquet files
- [ ] Add README for data_lake structure

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

- [ ] Create `export_service.py`
- [ ] Query events ordered by `(created_at, id)`
- [ ] Convert to pandas DataFrame
- [ ] Write `.parquet` file

### Partitioning

- [ ] Extract year, month, day
- [ ] Group by partitions
- [ ] Write partitioned files
- [ ] Ensure directory auto-creation

### API Access (temporary)

- [ ] Add `/inventory/export` endpoint
- [ ] Return export metadata (rows, partitions)

### Validation

- [ ] Manually create events
- [ ] Run export endpoint
- [ ] Verify file structure with `tree`
- [ ] Load parquet with pandas and inspect

---

## EPIC 3 — Incremental Pipeline

### Concept

Export only new events, not everything.

### Implementation

- [ ] Add `last_exported_at` tracking
- [ ] Filter query: `created_at > last_exported_at`
- [ ] Store checkpoint locally (file or table)
- [ ] Update checkpoint after export

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

- [ ] Add CLI script: `python scripts/export_events.py`
- [ ] Ensure same input → same output
- [ ] Add logging to export process
- [ ] Handle empty export gracefully

---

## EPIC 5 — Data Validation

### Goal

Ensure exported data is correct.

### Tasks

- [ ] Verify row counts match DB
- [ ] Validate schema consistency
- [ ] Ensure no duplicate `event_id`
- [ ] Add simple validation script

---

## EPIC 6 — Testing (Lightweight)

Optional but strong.

- [ ] Test export creates files
- [ ] Test partition structure
- [ ] Test incremental logic
- [ ] Test idempotent export

---

## EPIC 7 — Logging & Observability

### Extend your logger

- [ ] Log export start
- [ ] Log export completion
- [ ] Log number of rows exported
- [ ] Log partition counts

---

## EPIC 8 — Performance Basics

Not optimization, just awareness.

- [ ] Avoid loading unnecessary columns
- [ ] Ensure batch export is efficient
- [ ] Keep memory usage reasonable

---

## Milestone Definition (Epoch 2 COMPLETE)

You are done when:

- [ ] Events exported to Parquet
- [ ] Partitioned by date
- [ ] Incremental export working
- [ ] Pipeline reproducible
- [ ] Data validated

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
