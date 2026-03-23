from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_LAKE_ROOT = Path(os.getenv("DATA_LAKE_ROOT", BASE_DIR / "data_lake"))
INVENTORY_EVENTS_ROOT = DATA_LAKE_ROOT / "inventory_events"
CHECKPOINT_FILE = DATA_LAKE_ROOT / "checkpoints.json"