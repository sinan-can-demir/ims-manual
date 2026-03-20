from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models.enums import EventType

model_config = ConfigDict(from_attributes=True)


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
