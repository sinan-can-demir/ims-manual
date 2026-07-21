# app/config.py

import os
from pathlib import Path

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
FEATURE_STORE_PATH = Path(os.getenv("FEATURE_STORE_PATH", BASE_DIR / "feature_store"))
MODELS_DIR = Path(os.getenv("MODELS_DIR", BASE_DIR / "models"))

# -------------------------
# Model Registry (MLflow)
# -------------------------
# SQLite-backed by default (single file, no server to run) — MLflow's plain
# filesystem store is in maintenance mode and no longer supports the model
# registry. Requires `pip install -r requirements-train.txt`; not part of
# the API image (see docs/model-registry.md).
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", f"sqlite:///{BASE_DIR / 'mlflow.db'}")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "prophet-demand-forecasting")
