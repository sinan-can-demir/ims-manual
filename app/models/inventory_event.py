from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Index
from sqlalchemy.sql import func

from app.models.enums import EventType
from app.database import Base


class InventoryEvent(Base):
    __tablename__ = "inventory_events"

    __table_args__ = (
        Index("ix_inventory_events_product_id", "product_id"),
        Index("ix_inventory_events_created_at", "created_at"),
        Index("ix_inventory_events_product_created", "product_id", "created_at"),
    )

    id = Column(Integer, primary_key=True)

    event_id = Column(String, unique=True, nullable=False)

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    event_type = Column(
        Enum(EventType, name="event_type_enum"),
        nullable=False
    )

    quantity = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
