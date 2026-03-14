from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from app.models.inventory_event import InventoryEvent
from app.models.product import Product
from app.models.enums import EventType


def record_event(db: Session, product_id: int, event_type: EventType, quantity: int):

    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if event_type == EventType.SALE:

        current_inventory = (
            db.query(func.sum(InventoryEvent.quantity))
            .filter(InventoryEvent.product_id == product_id)
            .scalar()
        ) or 0

        if quantity > current_inventory:
            raise HTTPException(
                status_code=400,
                detail="Not enough inventory for sale"
            )

        quantity = -quantity

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