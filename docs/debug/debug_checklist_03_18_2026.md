# IMS — Inventory Hardening Debug Checklist (3/18/2026)

> **Last reviewed:** 3/20/2026
> **Overall progress:** ~80% complete (Phase 1: 100%, Phase 2: 80%, Phase 3: 65%, Bonus: 70%)

---

## PHASE 1 — CRITICAL CORRECTNESS (MUST FIX FIRST)

### Event Quantity Normalization (DATA CORRUPTION BUG)

- [x] Define clear quantity rules per event type
- [x] Enforce: PURCHASE / RETURN must be **positive only**
- [x] Enforce: SALE / DAMAGE must be **positive input → negative internal**
- [x] Allow ADJUSTMENT to be positive or negative (explicitly)
- [x] Add `normalize_quantity(event_type, quantity)` helper in service layer
- [x] Replace all direct quantity usage with normalized value
- [x] Add validation error (400) for invalid sign usage
- [x] Write tests:
  - [x] SALE with negative input → should fail
  - [x] PURCHASE with negative input → should fail
  - [x] ADJUSTMENT negative → allowed
  - [x] Zero quantity → rejected

---

### Single Source of Truth Decision

- [x] Decide: `inventory_events` = source of truth
- [x] Decide: `inventory_state` = projection
- [x] Update `get_inventory()` to read from `inventory_state`
- [x] Remove SUM(event) logic from normal read path
- [ ] (Optional) create reconciliation function:

```bash
WRITE:
  events → append
  state  → update

READ:
  state → return
```

- [x] `recompute_inventory_from_events(product_id)`
- [x] Ensure service writes:
  - [x] insert event
  - [x] update projection
- [x] Add test:
  - [x] projection matches expected after sequence of events

---

### Duplicate SKU Handling

- [x] Wrap `db.commit()` in try/except
- [x] Catch `IntegrityError`
- [x] Rollback session on error
- [x] Return HTTP 409 (Conflict)
- [x] Add test:
  - [x] creating duplicate SKU returns 409

---

## PHASE 2 — SYSTEM RELIABILITY

### Test Database Isolation

- [x] Remove hardcoded DB URL from `tests/conftest.py`
- [x] Use environment variable for test DB
- [x] Add `.env.test` or override in pytest
- [x] Option A (recommended now):
  - [x] Use SQLite for unit tests
- [ ] Option B (later):
  - [ ] Spin up Postgres container for tests
- [x] Ensure:
  - [x] tests create tables automatically
  - [x] tests teardown cleanly

---

### Startup / Migration Consistency

- [x] Ensure migrations run automatically on startup OR documented clearly
- [x] Option A:
  - [x] Add migration step in `docker-compose`
  - This part is done. When we use `docker compose up` command the migrations start automatically.
- [x] Option B:
  - [x] Add `Makefile` command: `make migrate`
- [x] Update README with exact startup steps
- [x] Verify:
  - [x] fresh clone → works without manual fixes

---

### README Sync

- [x] Remove non-existing endpoints from README
- [x] OR implement missing endpoints:
  - [x] GET /products (NOT IMPLEMENTED - removed from docs)
  - [x] GET /products/{id} (NOT IMPLEMENTED - removed from docs)
- [x] Update inventory endpoints to:
  - [x] POST /inventory/events
  - [x] GET /inventory/{product_id}
- [x] Add example request/response payloads
- [x] Add "How to run locally" section (accurate)

---

## PHASE 3 — PRODUCTION HARDENING

### Concurrency-Safe Oversell Protection

- [x] Wrap inventory operation in DB transaction
- [x] Use `SELECT ... FOR UPDATE` on `inventory_state`
- [x] Lock row before checking quantity
- [x] Re-check available stock inside transaction
- [x] Update quantity atomically
- [x] Commit transaction
- [ ] Add test (later or simulated):
  - [ ] concurrent sales do not oversell

Refactored `record_event` function is constructed as following:

```bash
1. Check duplicate (idempotency)
2. Normalize quantity → delta
3. Validate product exists
4. Lock inventory row (CRITICAL)
5. Compute new quantity
6. Validate (no oversell)
7. Insert event
8. Update projection
9. Commit transaction
```

---

### Clean Service Boundaries

- [x] Route should accept Pydantic schema only
- [ ] Remove ORM object creation from route
- [x] Service should construct ORM model
- [x] Update type hints:
  - [x] service takes `ProductCreate`, not `Product`
- [~] Refactor inventory routes similarly if needed (inventory routes done, products route partially)

---

### Response Models (API CONTRACT)

- [x] Add `response_model=` to:
  - [x] POST /products
  - [x] POST /inventory/events
  - [x] GET /inventory/{product_id}
- [x] Ensure schemas match actual DB output
- [x] Set correct status codes:
  - [x] POST /products → 201
  - [x] POST /inventory/events → 201

---

### Deterministic Event Listing

- [x] Add ordering:
  - [x] `ORDER BY created_at ASC, id ASC`
- [ ] Add pagination params:
  - [ ] `limit`
  - [ ] `offset`
- [ ] Update endpoint signature
- [ ] Add tests:
  - [ ] ordering is consistent
  - [ ] pagination works

---

### Pydantic v2 Cleanup

- [x] Replace `class Config` with:
  - [x] `model_config = ConfigDict(from_attributes=True)`
- [x] Remove deprecation warnings
- [x] Run pytest to confirm clean output

---

## BONUS (OPTIONAL BUT HIGH VALUE)

### Idempotency Safety (if not complete)

- [x] Ensure `event_id` is unique
- [x] Reject duplicate events cleanly
- [x] Add test:
  - [x] same event_id → no duplicate insert

---

### Test Coverage Expansion

- [x] Add inventory flow test:
  - [x] purchase → sale
  - [ ] return → damage (not tested)
- [x] Add edge case tests:
  - [x] zero inventory sale → fail
  - [ ] large adjustments (not tested)
- [x] Add negative scenarios
  - [x] idempotency
  - [ ] other negative scenarios (partial)

---

## Suggested Execution Strategy

Do NOT jump around. Follow this order strictly:

1. Quantity normalization
2. Inventory read consistency
3. Duplicate SKU handling
4. Tests + DB isolation
5. README + startup fix
6. Concurrency locking
7. Cleanup + polish

---

## Pro Tip (very important)

Commit after each block:

```bash
git commit -m "fix: normalize inventory event quantities"
git commit -m "refactor: use inventory_state as read model"
git commit -m "fix: handle duplicate SKU with 409 response"
```
