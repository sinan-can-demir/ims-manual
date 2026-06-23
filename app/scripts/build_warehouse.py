# app/scripts/build_warehouse.py

from app.database import SessionLocal
from app.services.warehouse_service import build_warehouse
from app.config import WAREHOUSE_END_DATE, WAREHOUSE_START_DATE
import os

def main() -> None:
    start_date = os.getenv("WAREHOUSE_START_DATE", "2020-01-01")
    end_date = os.getenv("WAREHOUSE_END_DATE", "2030-12-31")
    db = SessionLocal()
    try:
        build_warehouse(db, start_date=start_date, end_date=end_date)
    finally:
        db.close()


if __name__ == "__main__":
    main()