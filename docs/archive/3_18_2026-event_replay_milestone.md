# IMS Milestone --- 03/18/2026

## Focus: Event Replay System (Foundation for Data Platform)

------------------------------------------------------------------------

## 🎯 Goal

Introduce an **event replay system** that can reconstruct inventory
state from historical events.

This enables:

-   Deterministic rebuilding of state
-   Debugging historical inconsistencies
-   Foundation for data pipelines and ML

------------------------------------------------------------------------

## 🧠 Concepts

### Event Replay

    State = fold(events)

Rebuild inventory by replaying all events in order.

------------------------------------------------------------------------

## 🏗️ Tasks

### Core Implementation

-   [ ] Create replay service (`event_replay_service.py`)
-   [ ] Fetch events ordered by `created_at`
-   [ ] Apply events sequentially to compute inventory
-   [ ] Support replay for single product

------------------------------------------------------------------------

### API Layer

-   [ ] Add endpoint: `GET /api/inventory/replay/{product_id}`
-   [ ] Return reconstructed inventory
-   [ ] Compare with current projection

------------------------------------------------------------------------

### Validation

-   [ ] Ensure replay result == current inventory
-   [ ] Add pytest for replay correctness

------------------------------------------------------------------------

## 🧪 Testing

-   [ ] Replay after multiple events
-   [ ] Replay after duplicate event_id
-   [ ] Replay consistency check

------------------------------------------------------------------------

## 📌 Expected Outcome

-   Inventory can be rebuilt from events
-   Replay matches current system state
-   System becomes fully deterministic

------------------------------------------------------------------------

## 🚀 Next Step Preview

-   Data export (Parquet)
-   Warehouse modeling
-   Kafka streaming
