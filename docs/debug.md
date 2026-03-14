# Debug Notes

## 3/14/2026

### BUG #1

[x] sqlalchemy.exc.CompileError: PostgreSQL ENUM type requires a name.

- This is a very common SQLAlchemy + PostgreSQL Enum issue. PostgreSQL requires names for Enums but SQLAlchemy doesn't create them unless you make it.
    
- To solve this we added this to `app/models/inventory_event.py`
    
```py
    event_type = Column(
    Enum(EventType, name="event_type_enum"),
    nullable=False)
```

This solves the problm, docker composes up successfully.