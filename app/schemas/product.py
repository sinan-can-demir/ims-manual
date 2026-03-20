from pydantic import BaseModel, ConfigDict
from datetime import datetime

model_config = ConfigDict(from_attributes=True)

class ProductCreate(BaseModel):
    name: str
    sku: str


class ProductResponse(BaseModel):
    id: int
    name: str
    sku: str
    created_at: datetime