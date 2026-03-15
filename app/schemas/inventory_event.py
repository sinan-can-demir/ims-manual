from pydantic import BaseModel
from app.models.enums import EventType


class InventoryEventCreate(BaseModel):
    product_id: int
    event_type: EventType
    quantity: int

class InventoryEventResponse(BaseModel):
    id: int
    product_id: int
    event_type: str
    quantity: int

    class Config:
        from_attributes = True