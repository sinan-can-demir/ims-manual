from pydantic import BaseModel
from datetime import datetime
from app.models.enums import EventType


class InventoryEventCreate(BaseModel):
    product_id: int
    event_type: EventType
    quantity: int
    event_id: str

class InventoryEventResponse(BaseModel):
    id: int
    product_id: int
    event_type: EventType
    quantity: int
    event_id: str
    created_at: datetime

    class Config:
        from_attributes = True