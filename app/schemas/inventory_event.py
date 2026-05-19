# app/schemas/inventory_event.py

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models.enums import EventType


class InventoryEventCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: int
    event_type: EventType
    quantity: int
    event_id: str


class InventoryEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    event_type: EventType
    quantity: int
    event_id: str
    created_at: datetime