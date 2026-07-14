from enum import Enum


class EventType(str, Enum):
    """
    Enumeration for inventory event types.
    """

    PURCHASE = "PURCHASE"
    SALE = "SALE"
    DAMAGE = "DAMAGE"
    ADJUSTMENT = "ADJUSTMENT"
    RETURN = "RETURN"
