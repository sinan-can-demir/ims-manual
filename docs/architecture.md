# Project Architecture Design Notes

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