# schemas/inventory_state.py

from pydantic import BaseModel, ConfigDict

class InventoryStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: int
    quantity: int