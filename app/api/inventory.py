from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.inventory_event import InventoryEventCreate
from app.services.inventory_service import record_event, get_inventory
from app.models.enums import EventType

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/purchase", status_code=201)
def purchase_stock(
    event: InventoryEventCreate,
    db: Session = Depends(get_db),
):
    return record_event(db, event.product_id, EventType.PURCHASE, event.quantity)


@router.post("/sale", status_code=201)
def sell_stock(
    event: InventoryEventCreate,
    db: Session = Depends(get_db),
):
    return record_event(db, event.product_id, EventType.SALE, event.quantity)


@router.get("/{product_id}")
def inventory_level(product_id: int, db: Session = Depends(get_db)):
    return {"product_id": product_id, "inventory": get_inventory(db, product_id)}