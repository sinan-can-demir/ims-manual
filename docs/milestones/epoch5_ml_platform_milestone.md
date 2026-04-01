# IMS Milestone — Epoch 5 — ML Platform

## Date: 2026-03-30
## Focus: Build an ML Layer on Top of the Data Warehouse

---

## 🎯 Goal

Introduce a **machine learning layer** that transforms historical inventory
events into demand forecasts and actionable restock recommendations.

This enables:

- Predicting how many units a product will sell in the next 7 days
- Detecting when a stockout is likely to happen before it occurs
- Generating restock recommendations with quantities and deadlines
- Building the foundation for automated inventory intelligence

---

## 🧠 How ML Fits Into IMS

Most beginners jump straight to model training. That is the wrong order.

In real ML engineering, the work breaks down roughly like this:

```
Feature Engineering   ~50%   (transforming raw data into model inputs)
Model Training        ~20%   (actually fitting the model)
Model Serving         ~20%   (connecting the model to your API)
Monitoring / Retraining ~10% (keeping the model accurate over time)
```

This epoch follows that order deliberately. A well-engineered feature
table with a simple model will outperform a sophisticated model built
on raw, unreliable data every time.

The full data flow for Epoch 5:

```
inventory_events (source of truth)
        ↓
data_lake/ (Parquet exports)
        ↓
warehouse/ (dbt models — dim_products, fact_inventory_events)
        ↓
feature_store/ (new — Block 1)
        ↓
models/ (trained Prophet model — Block 2)
        ↓
GET /api/forecast/{product_id} (new — Block 3)
        ↓
GET /api/restock/{product_id}  (new — Block 4)
```

---

## 🧠 Tool Decision: Prophet

**Chosen model:** Facebook Prophet for demand forecasting.

**Why not a neural network or LSTM:**
Neural networks require large datasets to generalize. Your event log
is small and structured. Using a neural network here would be
overengineering — it would perform worse than a simpler model and be
much harder to debug and explain.

**Why not ARIMA:**
ARIMA is a valid choice but requires manual tuning of (p, d, q)
parameters and does not handle seasonality automatically. For a
beginner-friendly first forecasting model, Prophet is the better
starting point.

**Why Prophet:**
- Designed specifically for business time series (sales, demand)
- Handles weekly and yearly seasonality automatically
- Handles missing data and outliers gracefully
- Requires almost no hyperparameter tuning to get a reasonable baseline
- Used in production at many companies for exactly this use case
- Output is interpretable — you can see trend, seasonality, and
  uncertainty intervals clearly

**Progression:**
```
Epoch 5 — Prophet baseline model
              ↓
Future     — replace or augment with gradient boosting (LightGBM)
              ↓
Future     — add feature importance, model versioning, A/B testing
```

---

## 🏗️ Target Architecture

### New directories

```
app/
  services/
    feature_service.py       (Block 1 — feature engineering)
    forecast_service.py      (Block 2 — model training and loading)
    restock_service.py       (Block 4 — recommendation logic)
  api/
    forecast.py              (Block 3 — forecast and restock endpoints)
  schemas/
    forecast.py              (Pydantic response schemas)
  scripts/
    build_features.py        (CLI — build feature store)
    train_model.py           (CLI — train and save model)

feature_store/               (new directory at project root)
  daily_sales.parquet        (one row per product per day)

models/                      (new directory at project root)
  prophet_{product_id}.pkl   (one trained model per product)
```

### New API endpoints

```
GET /api/forecast/{product_id}    — 7-day demand forecast
GET /api/restock/{product_id}     — restock recommendation
```

---

## 🏗️ Tasks

---

### BLOCK 1 — Feature Engineering (1.5 hours)

**The most important block. Do not skip ahead.**

Feature engineering is the process of transforming raw event data into
a structured table that a model can learn from. The quality of your
features determines the quality of your model — not the algorithm.

**New file:** `app/services/feature_service.py`

#### What you are building

A `daily_sales` feature table with one row per product per day:

| product_id | date       | units_sold | units_purchased | net_delta | rolling_avg_7d | stockout_flag |
|------------|------------|------------|-----------------|-----------|----------------|---------------|
| 1          | 2026-03-14 | 15         | 0               | -15       | 12.4           | 0             |
| 1          | 2026-03-15 | 0          | 100             | 100       | 10.8           | 0             |

#### Feature definitions

| Feature | Type | Definition | Why it matters |
|---|---|---|---|
| `units_sold` | int | SUM of SALE + DAMAGE quantities for the day (as positive numbers) | Direct demand signal |
| `units_purchased` | int | SUM of PURCHASE + RETURN quantities for the day | Supply signal |
| `net_delta` | int | SUM of all quantity deltas for the day | Overall stock movement |
| `rolling_avg_7d` | float | 7-day rolling mean of `units_sold` | Smoothed demand trend — reduces noise |
| `stockout_flag` | int | 1 if inventory_state.quantity == 0 at end of day, else 0 | Flags lost sales opportunities |

#### Implementation steps

- [x] Install Prophet and joblib:
  ```bash
  pip install prophet joblib
  ```
- [x] Add `prophet` and `joblib` to `requirements.txt`
- [x] Create `feature_store/` directory at project root
- [x] Add `feature_store/*.parquet` to `.gitignore`
- [ ] Write `feature_service.py`:
  - Read `fact_inventory_events` from warehouse using DuckDB
  - Aggregate by `(product_id, date_id)` to get daily totals
  - Compute `rolling_avg_7d` using pandas `.rolling(7).mean()`
  - Join with `inventory_state` to get `stockout_flag`
  - Write result to `feature_store/daily_sales.parquet`
- [x] Add `build_features()` function that orchestrates the above
- [x] Create CLI script `app/scripts/build_features.py`
- [x] Add Makefile target:
  ```makefile
  features:
      python -m app.scripts.build_features
  ```
- [x] Verify output manually:
  ```python
  import pandas as pd
  df = pd.read_parquet("feature_store/daily_sales.parquet")
  print(df.head(20))
  print(df.dtypes)
  ```

#### Key concept: why rolling averages matter

Raw daily sales are noisy. A product might sell 0 units on Monday and
50 on Friday. A 7-day rolling average smooths this into a stable trend
signal. Without it, your model would try to learn noise instead of
the underlying pattern.

```
Raw:     0, 50, 10, 0, 30, 20, 5
Rolling: —   —   —   —  18  18  16
```

**Commit:**
```bash
git commit -m "feat(ml): add feature engineering service and daily_sales table"
```

---

### BLOCK 2 — Model Training (1.5 hours)

**New file:** `app/services/forecast_service.py`

#### What Prophet expects

Prophet requires a DataFrame with exactly two columns:

```
ds    — the date column (datetime)
y     — the value to forecast (units_sold)
```

That is it. Prophet handles trend detection, weekly seasonality, and
uncertainty intervals automatically from those two columns.

#### What you are building

A training function that:
1. Reads `feature_store/daily_sales.parquet`
2. Filters to a single product
3. Formats the DataFrame for Prophet
4. Fits the model
5. Saves the trained model to `models/prophet_{product_id}.pkl`

#### Implementation steps

- [x] Create `models/` directory at project root
- [x] Add `models/*.pkl` to `.gitignore`
- [x] Write `forecast_service.py`:

```python
import pandas as pd
import joblib
from prophet import Prophet
from pathlib import Path

FEATURE_STORE = Path("feature_store/daily_sales.parquet")
MODELS_DIR = Path("models")

def train_model(product_id: int) -> dict:
    """
    Train a Prophet demand forecasting model for a single product.
    Saves the model to models/prophet_{product_id}.pkl.
    Returns training summary metadata.
    """
    MODELS_DIR.mkdir(exist_ok=True)

    # 1. Load features for this product
    df = pd.read_parquet(FEATURE_STORE)
    product_df = df[df["product_id"] == product_id].copy()

    if len(product_df) < 7:
        raise ValueError(
            f"Product {product_id} has only {len(product_df)} days of data. "
            "Need at least 7 days to train a meaningful forecast."
        )

    # 2. Format for Prophet — requires 'ds' and 'y' columns
    prophet_df = product_df.rename(columns={
        "date": "ds",
        "units_sold": "y"
    })[["ds", "y"]]

    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])

    # 3. Train the model
    model = Prophet(
        yearly_seasonality=False,  # not enough data for yearly patterns yet
        weekly_seasonality=True,   # weekly patterns are realistic for inventory
        daily_seasonality=False,
        interval_width=0.95        # 95% confidence intervals on predictions
    )
    model.fit(prophet_df)

    # 4. Save the model to disk
    model_path = MODELS_DIR / f"prophet_{product_id}.pkl"
    joblib.dump(model, model_path)

    return {
        "product_id": product_id,
        "training_rows": len(prophet_df),
        "model_path": str(model_path),
    }


def train_all_models() -> list[dict]:
    """Train a model for every product in the feature store."""
    df = pd.read_parquet(FEATURE_STORE)
    product_ids = df["product_id"].unique().tolist()
    return [train_model(pid) for pid in product_ids]


def load_model(product_id: int) -> Prophet:
    """Load a trained model from disk. Raises if not found."""
    model_path = MODELS_DIR / f"prophet_{product_id}.pkl"
    if not model_path.exists():
        raise FileNotFoundError(
            f"No trained model found for product {product_id}. "
            "Run make train first."
        )
    return joblib.load(model_path)


def forecast(product_id: int, days: int = 7) -> pd.DataFrame:
    """
    Load the trained model for a product and generate a forecast.
    Returns a DataFrame with columns: ds, yhat, yhat_lower, yhat_upper.
    """
    model = load_model(product_id)

    # Prophet requires a future DataFrame with 'ds' column
    future = model.make_future_dataframe(periods=days)
    prediction = model.predict(future)

    # Return only the future rows (not historical)
    return prediction[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(days)
```

- [x] Create CLI script `app/scripts/train_model.py`:
  ```python
  from app.services.forecast_service import train_all_models

  def main():
      results = train_all_models()
      for r in results:
          print(r)

  if __name__ == "__main__":
      main()
  ```
- [x] Add Makefile target:
  ```makefile
  train:
      python -m app.scripts.train_model
  ```
- [x] Test the full pipeline manually:
  ```bash
  make export      # ensure data lake is populated
  make warehouse   # ensure warehouse is built
  make features    # build feature store
  make train       # train models
  ```
- [x] Verify a model file exists at `models/prophet_1.pkl`

#### Key concept: why we save models to disk

Retraining a model on every API request would be extremely slow and
wasteful. Instead, you train once (or on a schedule) and save the
trained model to disk. The API loads the saved model and uses it for
fast predictions. This pattern is called **offline training / online
serving** and is the standard approach in production ML systems.

**Commit:**
```bash
git commit -m "feat(ml): add Prophet model training and forecast service"
```

---

### BLOCK 3 — Model Serving (1 hour)

**Connect the trained model to your FastAPI API.**

This is where ML engineering meets backend engineering. The model is
worthless if it cannot be accessed. A well-designed serving layer
makes predictions available through a clean, typed API.

**New files:**
- `app/api/forecast.py`
- `app/schemas/forecast.py`

#### Pydantic schemas

**`app/schemas/forecast.py`:**

```python
from pydantic import BaseModel, ConfigDict
from datetime import date

class ForecastPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    date: date
    predicted_units: float
    lower_bound: float
    upper_bound: float

class ForecastResponse(BaseModel):
    product_id: int
    forecast_days: int
    predictions: list[ForecastPoint]
```

#### API router

**`app/api/forecast.py`:**

```python
from fastapi import APIRouter, HTTPException
from app.schemas.forecast import ForecastResponse, ForecastPoint
from app.services.forecast_service import forecast

router = APIRouter(prefix="/forecast", tags=["forecast"])

@router.get("/{product_id}", response_model=ForecastResponse)
def get_forecast(product_id: int, days: int = 7):
    """
    Return a demand forecast for the next N days.
    Requires a trained model — run make train first.
    """
    try:
        df = forecast(product_id, days=days)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    predictions = [
        ForecastPoint(
            date=row["ds"].date(),
            predicted_units=max(0, round(row["yhat"], 2)),
            lower_bound=max(0, round(row["yhat_lower"], 2)),
            upper_bound=max(0, round(row["yhat_upper"], 2)),
        )
        for _, row in df.iterrows()
    ]

    return ForecastResponse(
        product_id=product_id,
        forecast_days=days,
        predictions=predictions,
    )
```

#### Register the router

In `app/main.py`, add:
```python
from app.api.forecast import router as forecast_router
app.include_router(forecast_router, prefix="/api")
```

#### Implementation steps

- [x] Write `app/schemas/forecast.py`
- [x] Write `app/api/forecast.py`
- [x] Register router in `app/main.py`
- [x] Test manually via `http://localhost:8000/docs`
- [x] Verify response shape matches schema

#### Example response

```json
{
  "product_id": 1,
  "forecast_days": 7,
  "predictions": [
    {"date": "2026-03-31", "predicted_units": 12.4, "lower_bound": 8.1, "upper_bound": 16.7},
    {"date": "2026-04-01", "predicted_units": 14.2, "lower_bound": 9.8, "upper_bound": 18.6},
    ...
  ]
}
```

#### Key concept: why clamp predictions at 0

Prophet can produce negative predictions for `yhat` and `yhat_lower`
when demand is low or data is sparse. Negative units sold has no
business meaning. Always clamp forecast values at 0 before returning
them. This is a real-world detail that separates production-quality
serving from a notebook prototype.

**Commit:**
```bash
git commit -m "feat(ml): add forecast API endpoint with Pydantic response schema"
```

---

### BLOCK 4 — Restock Recommendation (1 hour)

**The business value layer. This is what makes the system intelligent.**

A raw forecast is useful. A restock recommendation is actionable.
The difference is combining the forecast with current inventory state
to answer the question a warehouse manager actually cares about:

> *"Do I need to order more stock, and if so, how much and by when?"*

**New file:** `app/services/restock_service.py`

#### Recommendation logic

```
current_inventory       — from inventory_state table
projected_demand_7d     — SUM of forecast predictions for next 7 days
safety_stock            — configurable buffer (default: 20% of projected demand)
recommended_order_qty   — max(0, projected_demand_7d + safety_stock - current_inventory)
stockout_in_days        — how many days until inventory hits 0 at current demand rate
```

#### Restock urgency levels

| Urgency | Condition |
|---|---|
| `OK` | current inventory > projected demand for 7 days |
| `LOW` | inventory covers 4–7 days of demand |
| `URGENT` | inventory covers fewer than 4 days of demand |
| `STOCKOUT` | inventory is already 0 |

#### Implementation steps

- [x] Write `app/services/restock_service.py`:

```python
from sqlalchemy.orm import Session
from app.services.inventory_service import get_inventory
from app.services.forecast_service import forecast

def get_restock_recommendation(db: Session, product_id: int) -> dict:
    """
    Combine current inventory with demand forecast to produce
    an actionable restock recommendation.
    """
    # 1. Get current inventory level
    current_qty = get_inventory(db, product_id)

    # 2. Get 7-day demand forecast
    forecast_df = forecast(product_id, days=7)
    projected_demand = max(0, forecast_df["yhat"].clip(lower=0).sum())

    # 3. Safety stock = 20% buffer on top of projected demand
    safety_stock = round(projected_demand * 0.20)

    # 4. Recommended order quantity
    recommended_qty = max(0, round(projected_demand + safety_stock - current_qty))

    # 5. Days of stock remaining at average daily demand rate
    daily_demand = projected_demand / 7
    if daily_demand > 0:
        days_of_stock = round(current_qty / daily_demand)
    else:
        days_of_stock = 999  # no demand projected

    # 6. Urgency classification
    if current_qty == 0:
        urgency = "STOCKOUT"
    elif days_of_stock < 4:
        urgency = "URGENT"
    elif days_of_stock < 7:
        urgency = "LOW"
    else:
        urgency = "OK"

    return {
        "product_id": product_id,
        "current_inventory": current_qty,
        "projected_demand_7d": round(projected_demand, 1),
        "safety_stock": safety_stock,
        "recommended_order_qty": recommended_qty,
        "days_of_stock_remaining": days_of_stock,
        "urgency": urgency,
    }
```

- [x] Add Pydantic schema `RestockResponse` to `app/schemas/forecast.py`
- [x] Add endpoint `GET /api/restock/{product_id}` to `app/api/forecast.py`
- [x] Test via `/docs`

#### Example response

```json
{
  "product_id": 1,
  "current_inventory": 35,
  "projected_demand_7d": 84.0,
  "safety_stock": 17,
  "recommended_order_qty": 66,
  "days_of_stock_remaining": 2,
  "urgency": "URGENT"
}
```

#### Key concept: safety stock

Safety stock is a buffer to absorb demand uncertainty. Without it,
you would order exactly what the model predicts — but models are never
perfectly accurate. A 20% buffer is a simple, industry-standard
starting point. In real systems this is tuned based on the cost of
stockouts vs. the cost of holding excess inventory.

**Commit:**
```bash
git commit -m "feat(ml): add restock recommendation service and API endpoint"
```

---

### BLOCK 5 — Tests (45 min)

**New file:** `tests/test_forecast.py`

The ML layer has different testing characteristics than the API layer.
You cannot test model *accuracy* in unit tests — that requires data
and evaluation metrics. What you can and should test:

- Feature engineering produces the correct shape and columns
- The forecast function returns the correct number of rows
- The restock logic classifies urgency correctly for known inputs
- The API returns 404 when no model is trained
- The API returns a valid response shape when a model exists

#### Tests to write

- [ ] `test_feature_columns` — daily_sales has expected columns
- [ ] `test_forecast_returns_n_days` — forecast(product_id, days=7) returns 7 rows
- [ ] `test_restock_urgency_stockout` — current_qty=0 → urgency=STOCKOUT
- [ ] `test_restock_urgency_ok` — large inventory → urgency=OK
- [ ] `test_forecast_endpoint_no_model` — returns 404 when model missing
- [ ] `test_restock_clamps_negative_qty` — recommended_order_qty never negative

**Commit:**
```bash
git commit -m "test: add forecast and restock service tests"
```

---

### BLOCK 6 — Documentation and Roadmap (15 min)

- [ ] Update `ROADMAP.md` — mark Epoch 5 in progress
- [ ] Update `README.md` — add new endpoints and pipeline steps
- [ ] Update `Last Updated` date
- [ ] Add pipeline documentation:
  ```
  make export      → export events to data lake
  make warehouse   → build warehouse (dbt)
  make features    → build feature store
  make train       → train Prophet models
  ```

**Commit:**
```bash
git commit -m "docs: add ML platform documentation and update roadmap"
```

---

## 🧪 Definition of Done

Epoch 5 is complete when:

- [x] `feature_store/daily_sales.parquet` builds correctly from warehouse data
- [x] `models/prophet_{product_id}.pkl` trains and saves without errors
- [x] `GET /api/forecast/{product_id}` returns a valid 7-day forecast
- [x] `GET /api/restock/{product_id}` returns urgency + recommended quantity
- [ ] All forecast and restock tests passing
- [ ] `make features && make train` runs end-to-end cleanly
- [ ] README documents the new pipeline steps

---

## 📋 Suggested Commit Order

```
feat(ml): add feature engineering service and daily_sales table
feat(ml): add Prophet model training and forecast service
feat(ml): add forecast API endpoint with Pydantic response schema
feat(ml): add restock recommendation service and API endpoint
test: add forecast and restock service tests
docs: add ML platform documentation and update roadmap
```

---

## ⚠️ Things to Watch Out For

**You need real data to train a meaningful model.**
Prophet needs at least 7 days of history per product. If your
event log is sparse, seed it with test data first using the API
before running `make features` and `make train`.

**Run the pipeline in order.**
The ML layer depends on the full upstream pipeline being populated:
```
make export → make warehouse (or make dbt-run) → make features → make train
```
If any step is skipped the next one will either fail or produce empty output.

**Prophet installation can be slow.**
It pulls Stan (a probabilistic programming framework) as a dependency.
Expect `pip install prophet` to take 2–5 minutes. This is normal.

**Models are not committed to git.**
Add `models/*.pkl` to `.gitignore`. Like Parquet files, trained models
are derived artifacts — always rebuildable from source data.

**Negative predictions are normal, not a bug.**
Prophet can predict negative values when demand is near zero. Clamping
at 0 in the serving layer (not the model) is the correct fix.

---

## 🚀 Next Milestone Preview

Once Epoch 5 is complete the system has a full ML intelligence layer.

The next session will begin **Epoch 6 — Application Layer**:
- Admin dashboard (FastAPI + Streamlit or lightweight frontend)
- Inventory monitoring with low stock alerts
- Restock recommendation UI
- Alerting on urgency thresholds (webhook or email)

Alternatively, if you want to go deeper on the engineering side:
- **Kafka** — real-time event streaming as an alternative write path
- This is the path toward a senior data engineering portfolio
