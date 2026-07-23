# Project Architecture Design Notes

> **Archived — early-stage notes.** Written 3/14–3/15/2026, covering only the
> initial event-sourcing core (`POST /api/products`). Predates ingestion,
> webhooks, the dashboard, the data warehouse/dbt, ML forecasting, and
> deployment — none of that is reflected here. Kept as project history, not
> as a current architecture reference — see `README.md`'s Architecture
> section and `ROADMAP.md` for the current state.

## 3/14/2026

I ran the test api for `post/api/products` (create product route) and it works. This shows the following pipeline is working successfully.

```bash
Client
 ↓
FastAPI Router
 ↓
Schema validation
 ↓
Service layer
 ↓
SQLAlchemy ORM
 ↓
Postgres container
 ↓
Commit success
 ↓
Response returned
```

New enums model is

```bash
class EventType(str, Enum):
    """
    Enumeration for inventory event types.
    """
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    DAMAGE = "DAMAGE"
    ADJUSTMENT = "ADJUSTMENT"
    RETURN = "RETURN"
```

meaning

```bash
Event	Effect
PURCHASE	inventory increases
SALE	inventory decreases
DAMAGE	inventory decreases
RETURN	inventory increases
ADJUSTMENT	manual correction
```

This will help us to consolidate different event services in one api.

The service will handle the logic

```bash
PURCHASE   → +quantity
SALE       → -quantity
DAMAGE     → -quantity
RETURN     → +quantity
ADJUSTMENT → ±quantity
```


## 3/15/2026

We will use an event-driven architecture. this will optimize our search allows us to scale systems up to millions. 

The key idea is The Core Idea: Events Are the Source of Truth. Traditional systems store state. We store every change of state as an event. 

Nothing is updated.

We only append events.

Inventory is computed as:

```py
inventory = SUM(events)
```

**Architecture Now**

```bash
WRITE PATH
Client
   ↓
POST /inventory/events
   ↓
InventoryEvent (append-only ledger)
   ↓
Projection Update
   ↓
InventoryState
                READ PATH
Client
   ↓
GET /inventory/{product_id}
   ↓
InventoryState
```

So:

```bash
writes → event log
reads  → projection
```

This pattern is called:

```bash
CQRS-lite

```
Command Query Responsibility Segregation.

Commands:

```bash
POST /inventory/events
```
Queries:

```bash
GET /inventory
```

With this system we can reconstruct inventory anytime

### Project Architecture now

```bash
                ┌──────────────┐
                │   Products   │
                └──────┬───────┘
                       │
                       ▼
               ┌──────────────┐
               │InventoryEvent│
               │  (ledger)    │
               └──────┬───────┘
                      │
                      ▼
               ┌──────────────┐
               │InventoryState│
               │ (projection) │
               └──────┬───────┘
                      │
                      ▼
               GET /inventory
```

---

Created `test_scripts` directory to keep the automated tests here.