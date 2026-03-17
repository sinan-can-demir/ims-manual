from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.inventory_event import InventoryEvent
from app.schemas.inventory_event import InventoryEventCreate
from app.services.inventory_service import record_event, get_inventory
from app.models.enums import EventType

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/events", status_code=201)
def create_inventory_event(
    event: InventoryEventCreate,
    db: Session = Depends(get_db)
):
    return record_event(
        db,
        event.product_id,
        event.event_type,
        event.quantity,
        event.event_id
    )


@router.get("/{product_id}")
def inventory_level(product_id: int, db: Session = Depends(get_db)):
    return {"product_id": product_id, "inventory": get_inventory(db, product_id)}

@router.get("/events/{product_id}")
def get_product_events(product_id: int, db: Session = Depends(get_db)):

    events = (
        db.query(InventoryEvent)
        .filter(InventoryEvent.product_id == product_id)
        .all()
    )

    return events