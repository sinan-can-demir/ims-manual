# 📦 IMS — Inventory Hardening Debug Checklist (3/18/2026)

> **Last reviewed:** 3/19/2026
> **Overall progress:** ~75% complete (Phase 1: ✅ 100%, Phase 2: ✅ 80%, Phase 3: ⏳ 60%, Bonus: ✅ 60%)

## 🔴 PHASE 1 — CRITICAL CORRECTNESS (MUST FIX FIRST)

### 🧮 Event Quantity Normalization (DATA CORRUPTION BUG)

* [✔] Define clear quantity rules per event type
* [✔] Enforce: PURCHASE / RETURN must be **positive only**
* [✔] Enforce: SALE / DAMAGE must be **positive input → negative internal**
* [✔] Allow ADJUSTMENT to be positive or negative (explicitly)
* [✔] Add `normalize_quantity(event_type, quantity)` helper in service layer
* [✔] Replace all direct quantity usage with normalized value
* [✔] Add validation error (400) for invalid sign usage
* [✔] Write tests:

  * [✔] SALE with negative input → should fail
  * [✔] PURCHASE with negative input → should fail
  * [✔] ADJUSTMENT negative → allowed
  * [✔] Zero quantity → rejected

---

### 📊 Single Source of Truth Decision

* [✔] Decide: `inventory_events` = source of truth
* [✔] Decide: `inventory_state` = projection
* [✔] Update `get_inventory()` to read from `inventory_state`
* [✔] Remove SUM(event) logic from normal read path
* [ ] (Optional) create reconciliation function:

```bash
WRITE:
  events → append
  state  → update

READ:
  state → return
```

  * [✔] `recompute_inventory_from_events(product_id)`
* [✔] Ensure service writes:

  * [✔] insert event
  * [✔] update projection
* [✔] Add test:

  * [✔] projection matches expected after sequence of events

---

### ⚠️ Duplicate SKU Handling

* [✔] Wrap `db.commit()` in try/except
* [✔] Catch `IntegrityError`
* [✔ ] Rollback session on error
* [✔] Return HTTP 409 (Conflict)
* [✔] Add test:

  * [✔] creating duplicate SKU returns 409

## 🟡 PHASE 2 — SYSTEM RELIABILITY

### 🧪 Test Database Isolation

* [✔] Remove hardcoded DB URL from `tests/conftest.py`
* [✔] Use environment variable for test DB
* [✔] Add `.env.test` or override in pytest
* [✔] Option A (recommended now):

  * [✔] Use SQLite for unit tests
* [ ] Option B (later):

  * [ ] Spin up Postgres container for tests
* [✔] Ensure:

  * [✔] tests create tables automatically
  * [✔] tests teardown cleanly

---

### 🚀 Startup / Migration Consistency

* [✔] Ensure migrations run automatically on startup OR documented clearly
* [✔] Option A:

  * [✔] Add migration step in `docker-compose`

  - This part is done. When we use `docker compose up` command the migrations start automatically.

* [✔] Option B:

  * [✔] Add `Makefile` command: `make migrate`
* [✔] Update README with exact startup steps
* [✔] Verify:

  * [✔] fresh clone → works without manual fixes

---

### 📘 README Sync

* [✔] Remove non-existing endpoints from README
* [✔] OR implement missing endpoints:

  * [x] GET /products (NOT IMPLEMENTED - removed from docs)
  * [x] GET /products/{id} (NOT IMPLEMENTED - removed from docs)
* [✔] Update inventory endpoints to:

  * [✔] POST /inventory/events
  * [✔] GET /inventory/{product_id}
* [✔] Add example request/response payloads
* [✔] Add "How to run locally" section (accurate)

---

## 🔵 PHASE 3 — PRODUCTION HARDENING

### 🔐 Concurrency-Safe Oversell Protection

* [✔] Wrap inventory operation in DB transaction
* [✔] Use `SELECT ... FOR UPDATE` on `inventory_state`
* [✔] Lock row before checking quantity
* [✔] Re-check available stock inside transaction
* [✔] Update quantity atomically
* [✔] Commit transaction
* [ ] Add test (later or simulated):

  * [ ] concurrent sales do not oversell

Refactored record_event function is constructured as following:

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

### 🧱 Clean Service Boundaries

* [ ] Route should accept Pydantic schema only
* [ ] Remove ORM object creation from route
* [ ] Service should construct ORM model
* [ ] Update type hints:

  * [x] service takes `ProductCreate`, not `Product` ✅
* [~] Refactor inventory routes similarly if needed (inventory routes done ✅, products route partially ❌)

---

### 📤 Response Models (API CONTRACT)

* [✔] Add `response_model=` to:

  * [✔] POST /products
  * [✔] POST /inventory/events
  * [✔] GET /inventory/{product_id}
* [✔] Ensure schemas match actual DB output
* [✔] Set correct status codes:

  * [✔] POST /products → 201
  * [✔] POST /inventory/events → 201

---

### 📜 Deterministic Event Listing

* [✔] Add ordering:

  * [✔] `ORDER BY created_at ASC, id ASC`
* [ ] Add pagination params:

  * [ ] `limit`
  * [ ] `offset`
* [ ] Update endpoint signature
* [ ] Add tests:

  * [ ] ordering is consistent
  * [ ] pagination works

---

### ⚙️ Pydantic v2 Cleanup

* [ ] Replace `class Config` with:

  * [ ] `model_config = ConfigDict(from_attributes=True)`
* [ ] Remove deprecation warnings
* [ ] Run pytest to confirm clean output

---

## 🟢 BONUS (OPTIONAL BUT HIGH VALUE)

### 🔁 Idempotency Safety (if not complete)

* [✔] Ensure `event_id` is unique
* [✔] Reject duplicate events cleanly
* [✔] Add test:

  * [✔] same event_id → no duplicate insert

---

### 🧪 Test Coverage Expansion

* [~] Add inventory flow test:

  * [✔] purchase → sale ✅
  * [ ] return → damage (not tested)
* [~] Add edge case tests:

  * [✔] zero inventory sale → fail ✅
  * [ ] large adjustments (not tested)
* [~] Add negative scenarios

  * [✔] idempotency ✅
  * [ ] other negative scenarios (partial)

---

# 🧭 Suggested Execution Strategy

Do NOT jump around.

👉 Follow this order strictly:

1. Quantity normalization
2. Inventory read consistency
3. Duplicate SKU handling
4. Tests + DB isolation
5. README + startup fix
6. Concurrency locking
7. Cleanup + polish

---

# 🧠 Pro Tip (very important)

Commit after each block:

```bash
git commit -m "fix: normalize inventory event quantities"
git commit -m "refactor: use inventory_state as read model"
git commit -m "fix: handle duplicate SKU with 409 response"
```
