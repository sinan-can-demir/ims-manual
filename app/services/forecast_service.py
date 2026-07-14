# app/services/forecast_service.py


import joblib
import pandas as pd
from prophet import Prophet

from app.config import FEATURE_STORE_PATH, MODELS_DIR
from app.core.logging import logger


def _ensure_directories() -> None:
    MODELS_DIR.mkdir(exist_ok=True)
    FEATURE_STORE_PATH.mkdir(exist_ok=True)


def train_model(product_id: int) -> dict:
    """
    Train a Prophet demand forecasting model for a single product.
    Saves the model to models/prophet_{product_id}.pkl.
    Returns training summary metadata.
    """
    _ensure_directories()

    logger.info("model_training_started", extra={"product_id": product_id})

    # 1. Load features for this product
    df = pd.read_parquet(FEATURE_STORE_PATH / "daily_sales.parquet")
    product_df = df[df["product_id"] == product_id].copy()

    if len(product_df) < 7:
        raise ValueError(
            f"Product {product_id} has only {len(product_df)} days of data. "
            "Need at least 7 days to train a meaningful forecast."
        )

    # 2. Format for Prophet — requires 'ds' and 'y' columns
    prophet_df = product_df.rename(columns={"date": "ds", "units_sold": "y"})[["ds", "y"]]

    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])

    # 3. Train the model
    model = Prophet(
        yearly_seasonality=False,  # not enough data for yearly patterns yet
        weekly_seasonality=True,  # weekly patterns are realistic for inventory
        daily_seasonality=False,
        interval_width=0.95,  # 95% confidence intervals on predictions
    )
    model.fit(prophet_df)

    # 4. Save the model to disk
    model_path = MODELS_DIR / f"prophet_{product_id}.pkl"
    joblib.dump(model, model_path)

    logger.info(
        "model_training_completed",
        extra={
            "product_id": product_id,
            "training_rows": len(prophet_df),
            "model_path": str(model_path),
        },
    )

    return {
        "product_id": product_id,
        "training_rows": len(prophet_df),
        "model_path": str(model_path),
    }


def train_all_models() -> list[dict]:
    """Train a model for every product in the feature store."""

    df = pd.read_parquet(FEATURE_STORE_PATH / "daily_sales.parquet")
    product_ids = df["product_id"].unique().tolist()

    return [train_model(pid) for pid in product_ids]


def load_model(product_id: int) -> Prophet:
    """Load a trained model from disk. Raises if not found."""
    _ensure_directories()

    model_path = MODELS_DIR / f"prophet_{product_id}.pkl"
    if not model_path.exists():
        raise FileNotFoundError(
            f"No trained model found for product {product_id}. Run make train first."
        )
    return joblib.load(model_path)


def forecast(product_id: int, days: int = 7) -> pd.DataFrame:
    """
    Load the trained model for a product and generate a forecast.
    Returns a DataFrame with columns: ds, yhat, yhat_lower, yhat_upper.
    """
    _ensure_directories()

    logger.info("forecast_started", extra={"product_id": product_id, "days": days})

    model = load_model(product_id)

    # Prophet requires a future DataFrame with 'ds' column
    future = model.make_future_dataframe(periods=days)
    prediction = model.predict(future)

    logger.info("forecast_completed", extra={"product_id": product_id})

    # Return only the future rows (not historical)
    return prediction[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(days)
