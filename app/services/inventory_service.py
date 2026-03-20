from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import EventType
from app.models.inventory_event import InventoryEvent
from app.models.inventory_state import InventoryState
from app.models.product import Product

from app.core.logging import logger

def normalize_quantity(event_type: EventType, quantity: int) -> int:
    if quantity == 0:
        raise HTTPException(status_code=400, detail="Quantity cannot be zero")

    if event_type in [EventType.PURCHASE, EventType.RETURN]:
        if quantity < 0:
            raise HTTPException(
                status_code=400,
                detail=f"{event_type.value} quantity must be positive",
            )
        return quantity

    if event_type in [EventType.SALE, EventType.DAMAGE]:
        if quantity < 0:
            raise HTTPException(
                status_code=400,
                detail=f"{event_type.value} quantity must be positive",
            )
        return -quantity

    if event_type == EventType.ADJUSTMENT:
        return quantity

    raise HTTPException(status_code=400, detail="Unsupported event type")


def get_inventory(db: Session, product_id: int) -> int:
    state = (
        db.query(InventoryState)
        .filter(InventoryState.product_id == product_id)
        .first()
    )
    return state.quantity if state else 0


def record_event(
    db: Session,
    product_id: int,
    event_type: EventType,
    quantity: int,
    event_id: str,
) -> InventoryEvent:
    # Check for existing event with same event_id for idempotency
    existing_event = (
        db.query(InventoryEvent)
        .filter(InventoryEvent.event_id == event_id)
        .first()
    )
    if existing_event:
        logger.info(
            "inventory_event_duplicate",
            extra={"event_id": event_id}
        )
        return existing_event

    # Normalize quantity based on event type
    delta = normalize_quantity(event_type, quantity)

    # Validate product existence
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        # Lock inventory state row for update or create if not exists
        state = (
            db.query(InventoryState)
            .filter(InventoryState.product_id == product_id)
            .with_for_update()      # Lock the row
            .first()
        )

        if state is None:
            state = InventoryState(product_id=product_id, quantity=0)
            db.add(state)
            db.flush()

        # Calculate new inventory level
        new_quantity = state.quantity + delta
        if new_quantity < 0 and event_type in [EventType.SALE, EventType.DAMAGE]:
            
            logger.warning(
                "inventory_oversell_blocked",
                extra={
                "product_id": product_id,
                "attempted_quantity": delta,
                "current_quantity": state.quantity
                }
            )
            
            raise HTTPException(status_code=400, detail="Insufficient inventory")

        # Record the event
        event = InventoryEvent(
            product_id=product_id,
            event_type=event_type,
            quantity=delta,
            event_id=event_id,
        )

        # Add event and update inventory state atomically
        db.add(event)

        # Update inventory state
        state.quantity = new_quantity

        # Commit transaction
        db.commit()
        db.refresh(event)

        logger.info(
            "inventory_event_created",
            extra={
                "product_id": product_id,
                "event_type": event_type.value,
                "quantity": delta,
                "event_id": event_id
            }
        )

        return event

    except IntegrityError:
        db.rollback()

        logger.warning(
            "inventory_event_integrity_error",
            extra={"event_id": event_id}
        )
        
        # Check if the failure was due to a duplicate event_id (idempotency)
        existing_event = (
            db.query(InventoryEvent)
            .filter(InventoryEvent.event_id == event_id)
            .first()
        )

        # If the event already exists, return it instead of raising an error
        if existing_event:
            return existing_event

        # If the event doesn't exist, it means the failure was due to another reason (e.g., database error)
        raise