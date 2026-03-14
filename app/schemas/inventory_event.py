from pydantic import BaseModel


class InventoryEventCreate(BaseModel):
    product_id: int
    quantity: int


class InventoryEventResponse(BaseModel):
    id: int
    product_id: int
    event_type: str
    quantity: int

    class Config:
        from_attributes = True