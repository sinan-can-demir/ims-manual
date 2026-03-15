from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from app.models.inventory_event import InventoryEvent
from app.models.inventory_state import InventoryState
from app.models.product import Product
from app.models.enums import EventType


def record_event(db: Session, product_id: int, event_type: EventType, quantity: int):
    """
    Records an inventory event and updates the inventory level accordingly.
    For SALE and DAMAGE events, the quantity is subtracted from inventory.
    For PURCHASE and RETURN events, the quantity is added to inventory.
    For ADJUSTMENT events, the quantity can be positive or negative.
    ARGS:
        db: Database session
        product_id: ID of the product
        event_type: Type of the inventory event
        quantity: Quantity of the event
    RETURNS:        
        The created InventoryEvent object
    Raises:
        HTTPException: If the product does not exist or if there is not enough inventory for SALE/DAMAGE events
    """
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    state = db.query(InventoryState).filter(
        InventoryState.product_id == product_id
    ).first()

    current_inventory = state.quantity if state else 0

    # Inventory decreasing events
    if event_type in {EventType.SALE, EventType.DAMAGE}:

        if quantity > current_inventory:
            raise HTTPException(
                status_code=400,
                detail="Not enough inventory"
            )

        quantity = -quantity

    # Inventory increasing events
    elif event_type in {EventType.PURCHASE, EventType.RETURN}:
        quantity = quantity

    # Adjustment can be positive or negative
    elif event_type == EventType.ADJUSTMENT:
        pass

    event = InventoryEvent(
        product_id=product_id,
        event_type=event_type,
        quantity=quantity
    )

    # Create projection row if it doesn't exist
    if not state:
        state = InventoryState(
            product_id=product_id,
            quantity=0
        )
        db.add(state)

    # Update current inventory snapshot
    state.quantity += quantity

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


def get_inventory(db: Session, product_id: int):

    total = (
        db.query(func.sum(InventoryEvent.quantity))
        .filter(InventoryEvent.product_id == product_id)
        .scalar()
    )

    return total or 0