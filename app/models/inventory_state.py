# models/inventory_state.py

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database import Base


class InventoryState(Base):
    """
    Projection table representing the current inventory level
    for each product.

    This table is derived from inventory_events but stores the
    latest snapshot so we don't need to recompute sums every time.
    """

    __tablename__ = "inventory_state"

    # One row per product
    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)

    quantity = Column(Integer, nullable=False, server_default="0")

    # Optional relationship
    product = relationship("Product")
