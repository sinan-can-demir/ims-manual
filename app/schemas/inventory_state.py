# schemas/inventory_state.py

from pydantic import BaseModel


class InventoryStateResponse(BaseModel):
    product_id: int
    quantity: int

    class Config:
        from_attributes = True