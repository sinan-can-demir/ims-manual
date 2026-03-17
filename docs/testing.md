# IMS Event System

## Overview

The Inventory Management System (IMS) uses an **event-driven
architecture**.

Inventory is NOT stored directly.

Instead, it is derived from a sequence of events.

------------------------------------------------------------------------

## Core Principle

Inventory = SUM(events)

Where events include:

-   PURCHASE (+)
-   SALE (-)

------------------------------------------------------------------------

## Event Model

Each event contains:

-   product_id
-   event_type (PURCHASE / SALE)
-   quantity
-   event_id (for idempotency)
-   created_at

------------------------------------------------------------------------

## Idempotency

The system guarantees:

Same event_id → processed only once

This prevents:

-   duplicate purchases
-   double sales
-   data corruption

------------------------------------------------------------------------

## Inventory Calculation

Inventory is computed by:

1.  Fetching all events for a product

2.  Applying:

    -   PURCHASE → +quantity
    -   SALE → -quantity

------------------------------------------------------------------------

## Business Rules

-   Inventory cannot go below 0
-   SALE \> available inventory → rejected (400)

------------------------------------------------------------------------

## Testing Strategy

The system is validated using:

### Pytest

-   Product creation
-   Inventory flow
-   Oversell protection
-   Idempotency

### E2E Tests

-   Full system validation using Docker + curl

------------------------------------------------------------------------

## Guarantees

The system ensures:

-   Deterministic behavior
-   Idempotent event processing
-   Replayable history
-   Data integrity

------------------------------------------------------------------------

## Future Extensions

-   Event replay system
-   Kafka streaming
-   Data warehouse (fact_inventory_events)
-   ML forecasting