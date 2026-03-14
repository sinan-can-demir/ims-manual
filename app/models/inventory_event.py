from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func

from app.models.enums import EventType
from app.database import Base


class InventoryEvent(Base):
    __tablename__ = "inventory_events"

    id = Column(Integer, primary_key=True)

    product_id = Column(Integer, ForeignKey("products.id"))

    event_type = Column(
        Enum(EventType, name="event_type_enum"),
        nullable=False)

    quantity = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
