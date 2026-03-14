from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class InventoryEvent(Base):
    __tablename__ = "inventory_events"

    id = Column(Integer, primary_key=True)

    product_id = Column(Integer, ForeignKey("products.id"))

    event_type = Column(String)

    quantity = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
