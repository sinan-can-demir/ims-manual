from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from fastapi import HTTPException

from app.models.inventory_event import InventoryEvent
from app.models.inventory_state import InventoryState
from app.models.product import Product
from app.models.enums import EventType



def normalize_quantity(event_type: EventType, quantity: int) -> int:
    # Zero quantity doesn't make sense for any event type, so we reject it
    if quantity == 0:
        raise HTTPException(status_code=400, detail="Quantity must not be zero")

    # For PURCHASE and RETURN, quantity is added to inventory, so we return it as is
    if event_type in {EventType.PURCHASE, EventType.RETURN}:
        if quantity < 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")
        return quantity

    
    if event_type in {EventType.SALE, EventType.DAMAGE}:
        if quantity < 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")
        return -quantity

    if event_type == EventType.ADJUSTMENT:
        return quantity

    raise HTTPException(status_code=400, detail="Invalid event type")

def record_event(
    db: Session,
    product_id: int,
    event_type: EventType,
    quantity: int,
    event_id: str
):
    # 🔁 Idempotency check
    existing = (
        db.query(InventoryEvent)
        .filter(InventoryEvent.event_id == event_id)
        .first()
    )

    # If event with same event_id already exists, return it (idempotent)
    if existing:
        return existing

    product = db.query(Product).filter(Product.id == product_id).first()

    # 404 if product doesn't exist
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    state = db.query(InventoryState).filter(
        InventoryState.product_id == product_id
    ).first()

    delta = normalize_quantity(event_type, quantity)

    current_inventory = state.quantity if state else 0

    if event_type in {EventType.SALE, EventType.DAMAGE}:
        if abs(delta) > current_inventory:
            raise HTTPException(status_code=400, detail="Not enough inventory")

    event = InventoryEvent(
        product_id=product_id,
        event_type=event_type,
        quantity=delta,
        event_id=event_id
    )

    if not state:
        state = InventoryState(product_id=product_id, quantity=0)
        db.add(state)

    state.quantity += delta

    try:
        db.add(event)
        db.commit()
        db.refresh(event)

    except IntegrityError:
        db.rollback()

        existing = (
            db.query(InventoryEvent)
            .filter(InventoryEvent.event_id == event_id)
            .first()
        )

        # If another transaction inserted the same event_id, return that (idempotent)
        if existing:
            return existing

        # If we get here, it means the IntegrityError was due to something else, so we 
        # raise it to be handled by the global exception handler (500 error)
        raise

    return event


def get_inventory(db: Session, product_id: int):

    total = (
        db.query(func.sum(InventoryEvent.quantity))
        .filter(InventoryEvent.product_id == product_id)
        .scalar()
    )

    return total or 0