# IMS Development Milestone

Date: 2026-03-17 Focus: Event Store Hardening

Today we improve the core event system used by the inventory engine.

Goal: make the `inventory_events` table production-ready.

------------------------------------------------------------------------

# Tasks

## 1 --- Add Event Table Indexes

Event tables grow extremely fast. Indexes are required for performance.

Create indexes for:

-   product_id
-   created_at
-   (product_id, created_at)

Steps:

1.  Generate migration

``` bash
alembic revision -m "add inventory event indexes"
```

2.  Edit migration file

```{=html}
<!-- -->
```
    migrations/versions/<revision>.py

Add:

``` py
op.create_index(
    "ix_inventory_events_product_id",
    "inventory_events",
    ["product_id"]
)

op.create_index(
    "ix_inventory_events_created_at",
    "inventory_events",
    ["created_at"]
)

op.create_index(
    "ix_inventory_events_product_created",
    "inventory_events",
    ["product_id", "created_at"]
)
```

3.  Apply migration

``` bash
alembic upgrade head
```

------------------------------------------------------------------------

## 2 --- Make `product_id` NOT NULL

Inventory events must always belong to a product.

Update model:

``` py
product_id = Column(
    Integer,
    ForeignKey("products.id"),
    nullable=False
)
```

Generate migration:

``` bash
alembic revision --autogenerate -m "enforce product_id not null"
```

------------------------------------------------------------------------

## 3 --- Add Event Idempotency

Event systems must prevent duplicate events.

Example problem:

    SALE event processed twice
    ↓
    inventory becomes incorrect

Add column:

``` py
event_id = Column(String, unique=True, nullable=False)
```

This allows safe retrying of operations.

Migration:

``` bash
alembic revision --autogenerate -m "add event idempotency"
```

------------------------------------------------------------------------

## 4 --- Improve Inventory Projection

Verify projection logic updates `inventory_state` correctly.

Check event behavior:

  Event Type   Expected Behavior
  ------------ -------------------
  PURCHASE     increase quantity
  SALE         decrease quantity
  DAMAGE       decrease quantity
  ADJUSTMENT   modify quantity
  RETURN       increase quantity

Ensure that:

    inventory_state.quantity

always reflects the correct value after processing events.

------------------------------------------------------------------------

## 5 --- Add Pytest Test Suite

To ensure reliability of the event system, introduce automated tests.

Create a new directory:

    tests/

Suggested structure:

    tests/
    │
    ├── conftest.py
    ├── test_products.py
    ├── test_inventory_events.py
    └── test_inventory_projection.py

### Install testing dependencies

Add to project dependencies:

``` bash
pip install pytest pytest-asyncio httpx
```

------------------------------------------------------------------------

### Example API Test

`tests/test_products.py`

``` python
def test_create_product(client):

    response = client.post(
        "/api/products",
        json={
            "name": "Test Product",
            "sku": "TEST-1"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Product"
```

------------------------------------------------------------------------

### Example Event Test

`tests/test_inventory_events.py`

``` python
def test_purchase_event(client):

    product = client.post(
        "/api/products",
        json={
            "name": "Widget",
            "sku": "W1"
        }
    ).json()

    response = client.post(
        "/api/inventory/events",
        json={
            "product_id": product["id"],
            "event_type": "PURCHASE",
            "quantity": 10,
            "event_id": "evt_test_1"
        }
    )

    assert response.status_code == 201
```

------------------------------------------------------------------------

### Example Projection Test

`tests/test_inventory_projection.py`

``` python
def test_inventory_projection(client):

    product = client.post(
        "/api/products",
        json={"name": "Widget", "sku": "W2"}
    ).json()

    client.post("/api/inventory/events", json={
        "product_id": product["id"],
        "event_type": "PURCHASE",
        "quantity": 10,
        "event_id": "evt1"
    })

    client.post("/api/inventory/events", json={
        "product_id": product["id"],
        "event_type": "SALE",
        "quantity": 3,
        "event_id": "evt2"
    })

    inventory = client.get(f"/api/inventory/{product['id']}").json()

    assert inventory["quantity"] == 7
```

This test verifies that projection logic works correctly.

------------------------------------------------------------------------

## 6 --- Document Event System

Create documentation:

    docs/event_system.md

Explain:

-   event sourcing concept
-   `inventory_events` event log
-   `inventory_state` projection table
-   how inventory is calculated
-   how projections stay consistent

This documentation will help future contributors understand the
architecture.

------------------------------------------------------------------------

# Expected Outcome

After completing this milestone the system will have:

-   indexed event store
-   safer event processing
-   idempotent event handling
-   automated tests
-   stronger schema
-   documented architecture

This prepares the system for:

-   data lake exports
-   analytics warehouse
-   streaming pipelines
-   machine learning features

------------------------------------------------------------------------

# Status

## Database Hardening

-   [✔] Add event indexes
-   [✔] Enforce `product_id` NOT NULL
-   [✔] Add `event_id` idempotency
-   [✔] Add testing script (.sh) for new features.

## Inventory Logic

-   [ ] Verify projection logic

## Testing

-   [ ] Create `tests/` directory
-   [ ] Install pytest dependencies
-   [ ] Add product API test
-   [ ] Add inventory event test
-   [ ] Add projection test

## Documentation

-   [ ] Write `docs/event_system.md`
