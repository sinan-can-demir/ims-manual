# app/config.py

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------
# Data Lake
# -----------------
DATA_LAKE_ROOT = Path(os.getenv("DATA_LAKE_ROOT", BASE_DIR / "data_lake"))
INVENTORY_EVENTS_ROOT = DATA_LAKE_ROOT / "inventory_events"
CHECKPOINT_FILE = DATA_LAKE_ROOT / "checkpoints.json"

# ------------------
# Warehouse
# ------------------
WAREHOUSE_ROOT = Path(os.getenv("WAREHOUSE_ROOT", BASE_DIR / "warehouse"))
WAREHOUSE_START_DATE = os.getenv("WAREHOUSE_START_DATE", "2020-01-01")
WAREHOUSE_END_DATE = os.getenv("WAREHOUSE_END_DATE", "2030-12-31")

# -------------------
# Feature
# -------------------
FEATURE_STORE_PATH=Path(os.getenv("FEATURE_STORE_PATH", BASE_DIR / "feature_store"))
MODELS_DIR = Path(os.getenv("MODELS_DIR", BASE_DIR / "models"))