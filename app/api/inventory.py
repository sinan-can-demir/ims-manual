from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.inventory_event import InventoryEvent
from app.schemas.export import ExportMetadata
from app.schemas.inventory_event import InventoryEventCreate, InventoryEventResponse
from app.schemas.inventory_state import InventoryStateResponse
from app.services.export_service import export_inventory_events
from app.services.inventory_service import get_inventory, record_event
from app.services.replay_service import rebuild_inventory_state

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/events", response_model=InventoryEventResponse, status_code=201)
def create_inventory_event(event: InventoryEventCreate, db: Session = Depends(get_db)):
    return record_event(db, event.product_id, event.event_type, event.quantity, event.event_id)


@router.post("/replay")
def replay_inventory_projection(db: Session = Depends(get_db)):
    return rebuild_inventory_state(db)


@router.get("/events/{product_id}", response_model=list[InventoryEventResponse])
def get_product_events(
    product_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    events = (
        db.query(InventoryEvent)
        .filter(InventoryEvent.product_id == product_id)
        .order_by(InventoryEvent.created_at.asc(), InventoryEvent.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return events


@router.get("/{product_id}", response_model=InventoryStateResponse)
def inventory_level(product_id: int, db: Session = Depends(get_db)):
    return InventoryStateResponse(product_id=product_id, quantity=get_inventory(db, product_id))


@router.post("/export", response_model=ExportMetadata)
def export_inventory(db: Session = Depends(get_db)):
    return export_inventory_events(db, incremental=True)
