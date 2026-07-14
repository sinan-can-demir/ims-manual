from app.database import SessionLocal
from app.services.export_service import export_inventory_events


def main() -> None:
    db = SessionLocal()
    try:
        result = export_inventory_events(db, incremental=True)
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    main()
