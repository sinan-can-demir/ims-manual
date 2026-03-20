# schemas/inventory_state.py

from pydantic import BaseModel, ConfigDict

model_config = ConfigDict(from_attributes=True)


class InventoryStateResponse(BaseModel):
    product_id: int
    quantity: int