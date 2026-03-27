from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ProductCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    sku: str


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    sku: str
    created_at: datetime