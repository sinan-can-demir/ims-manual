from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from app.models.inventory_event import InventoryEvent


def record_event(db, product_id, event_type, quantity):
    """
    Records an inventory event (purchase or sale) and updates the inventory level.
    For sales, it checks if there is enough inventory before recording the event.
    
    Args:
        db (Session): Database session
        product_id (int): ID of the product
        event_type (str): Type of the event ("PURCHASE" or "SALE")
        quantity (int): Quantity of the event (positive for purchase, negative for sale)
    Returns:
        InventoryEvent: The recorded inventory event
    Raises:
        HTTPException: If there is not enough inventory for a sale
    """
    if event_type == "SALE":

        current_inventory = (
            db.query(func.sum(InventoryEvent.quantity))
            .filter(InventoryEvent.product_id == product_id)
            .scalar()
        ) or 0

        # Check if there is enough inventory for the sale
        if current_inventory < quantity:
            raise HTTPException(
                status_code=400,
                detail="Not enough inventory for sale"
            )

        quantity = -quantity

    # Record the inventory event
    event = InventoryEvent(
        product_id=product_id,
        event_type=event_type,
        quantity=quantity
    )

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