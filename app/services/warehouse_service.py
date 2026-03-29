# app/services/warehouse_service.py

import pandas as pd
import duckdb

from sqlalchemy.orm import Session
from app.models.product import Product
from app.config import WAREHOUSE_ROOT, INVENTORY_EVENTS_ROOT


def _ensure_directories() -> None:
    WAREHOUSE_ROOT.mkdir(parents=True, exist_ok=True)


def build_dim_products(db: Session) -> int:

    # 1. Query all products
    products = db.query(Product).all()
 
    # 2. Convert to DataFrame
    df = pd.DataFrame([{
        'product_id': p.id,
        'name': p.name,
        'sku': p.sku,
        'created_at': p.created_at
    } for p in products])

    # 3. Ensure warehouse directory exists
    _ensure_directories()

    # 4. Write to parquet
    file_path = WAREHOUSE_ROOT / "dim_products.parquet"
    df.to_parquet(file_path, index=False)

    return len(df)

def build_dim_dates(start_date, end_date) -> int:

    # 1. Get all dates from start_date to end_date
    dates = pd.date_range(start=start_date, end=end_date, freq="d")

    # 2. Build a DataFrame using dates
    df = pd.DataFrame({
        'date_id':     dates.strftime("%Y-%m-%d"),
        'year':        dates.year,
        'month':       dates.month,
        'day':         dates.day,
        'quarter':     dates.quarter,
        'day_of_week': dates.day_name(),
        'is_weekend':  dates.day_name().isin(["Saturday", "Sunday"])
    })

    # 3. Ensure data warehouse exists
    _ensure_directories()

    # 4. write to parquet
    file_path = WAREHOUSE_ROOT / "dim_dates.parquet"
    df.to_parquet(file_path, index=False)

    # 5. return the row count
    return len(df)

def build_fact_table() -> int:

    # 1. Connect to DuckDB in memory
    conn = duckdb.connect()

    # 2. Ensure directory exists
    _ensure_directories()

    # 3. Read inventory events from data_lake
    # This query has 2 scanning (FROM looks for events AND JOIN looks for products)
    # and one conditional check(ON) for product id. normally makes an O(m X n) complexity.
    # But DuckDB uses a hash join here — O(n + m) where n is events and m is products.
    # Products table is small so the hash table fits in memory entirely,
    # making this effectively O(n) in practice.
    result = conn.execute(f"""
    SELECT
        e.event_id,
        e.product_id,
        strftime(e.created_at, '%Y-%m-%d') AS date_id,
        e.event_type,
        e.quantity,
        e.created_at
    FROM read_parquet('{INVENTORY_EVENTS_ROOT}/**/*.parquet') e
    JOIN read_parquet('{WAREHOUSE_ROOT}/dim_products.parquet') p
        ON e.product_id = p.product_id
    """).df()  # .df() converts directly to pandas DataFrame

    # 4. write to warehouse/fact_inventory_events.parquet
    file_path = WAREHOUSE_ROOT / "fact_inventory_events.parquet"
    result.to_parquet(file_path,index=False)

    # 5. Close duckdb connection
    conn.close()

    # 6. Return the row count
    return len(result)

def build_warehouse(db: Session, start_date: str, end_date: str) -> bool:
    try:
        # 1. Ensure directory exists
        _ensure_directories()

        # 2. Build dim products, dim dates and fact tables.
        products_count = build_dim_products(db)
        dates_count = build_dim_dates(start_date, end_date)
        facts_count = build_fact_table()

        # 3. Print the row counts
        print(f"dim_products: {products_count} rows")
        print(f"dim_dates: {dates_count} rows")
        print(f"fact_inventory_events: {facts_count} rows")

        # 4. return true if run successfully
        return True

    except Exception as e:
        # Catch errors and return false
        print(f"Warehouse build failed: {e}")
        return False
