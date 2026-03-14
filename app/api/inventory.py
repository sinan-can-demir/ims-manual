from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.inventory_event import InventoryEventCreate
from app.services.inventory_service import record_event, get_inventory

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/purchase")
def purchase_stock(
    event: InventoryEventCreate,
    db: Session = Depends(get_db),
):
    return record_event(db, event.product_id, "PURCHASE", event.quantity)


@router.post("/sale")
def sell_stock(
    event: InventoryEventCreate,
    db: Session = Depends(get_db),
):
    return record_event(db, event.product_id, "SALE", -event.quantity)


@router.get("/{product_id}")
def inventory_level(product_id: int, db: Session = Depends(get_db)):
    return {"product_id": product_id, "inventory": get_inventory(db, product_id)}