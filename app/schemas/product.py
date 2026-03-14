from pydantic import BaseModel
from datetime import datetime


class ProductCreate(BaseModel):
    name: str
    sku: str


class ProductResponse(BaseModel):
    id: int
    name: str
    sku: str
    created_at: datetime

    class Config:
        from_attributes = True
