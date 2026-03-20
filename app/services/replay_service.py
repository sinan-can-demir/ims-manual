from collections import defaultdict
from sqlalchemy.orm import Session

from app.core.logging import logger

from app.models.inventory_event import InventoryEvent
from app.models.inventory_state import InventoryState


def rebuild_inventory_state(db: Session) -> dict:
    """
    Rebuilds the inventory_state projection from inventory_events.

    Returns a small summary for debugging/admin use.
    """
    # Get all events in chronological order
    events = (
        db.query(InventoryEvent)
        .order_by(InventoryEvent.created_at.asc(), InventoryEvent.id.asc())
        .all()
    )

    # Start fresh
    db.query(InventoryState).delete()

    # Aggregate quantities by product_id
    quantities = defaultdict(int)

    # Process events in order to rebuild state
    for event in events:
        quantities[event.product_id] += event.quantity

    # Create new InventoryState rows based on aggregated quantities
    rebuilt_rows = []

    # Append new rows for products that have events
    for product_id, quantity in quantities.items():
        rebuilt_rows.append(
            InventoryState(product_id=product_id, quantity=quantity)
        )

    # Bulk insert new state rows
    if rebuilt_rows:
        db.add_all(rebuilt_rows)

    # Commit the transaction to save changes
    db.commit()
    logger.info(
        "inventory_replay_completed",
        extra={
            "events_processed": len(events),
            "products_rebuilt": len(rebuilt_rows)
        }
    )

    # Return summary of the rebuild process
    return {
        "events_processed": len(events),
        "products_rebuilt": len(rebuilt_rows),
    }