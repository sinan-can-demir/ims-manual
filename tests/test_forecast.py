# tests/test_forecast.py

import os
from unittest.mock import patch

import pandas as pd
import pytest

from app.services.forecast_service import forecast
from app.services.restock_service import get_restock_recommendation

from .utils import create_product


def test_restock_urgency_stockout(client, db):
    product = create_product(client)
    pid = product["id"]

    # Mock forecast so we don't need a trained model
    mock_forecast_df = pd.DataFrame(
        {
            "ds": pd.date_range("2026-04-01", periods=7),
            "yhat": [15.0] * 7,
            "yhat_lower": [10.0] * 7,
            "yhat_upper": [20.0] * 7,
        }
    )

    with patch("app.services.restock_service.forecast", return_value=mock_forecast_df):
        # current inventory is 0 — no events added
        result = get_restock_recommendation(db, pid)

    assert result["urgency"] == "STOCKOUT"
    assert result["current_inventory"] == 0


def test_restock_urgency_ok(client, db):
    product = create_product(client)
    pid = product["id"]

    # Add a large purchase so inventory is well above projected demand
    client.post(
        "/api/inventory/events",
        json={
            "product_id": pid,
            "event_type": "PURCHASE",
            "quantity": 500,
            "event_id": "evt-test-ok",
        },
    )

    mock_forecast_df = pd.DataFrame(
        {
            "ds": pd.date_range("2026-04-01", periods=7),
            "yhat": [15.0] * 7,  # projected demand = 105 total
            "yhat_lower": [10.0] * 7,
            "yhat_upper": [20.0] * 7,
        }
    )

    with patch("app.services.restock_service.forecast", return_value=mock_forecast_df):
        result = get_restock_recommendation(db, pid)

    assert result["urgency"] == "OK"
    assert result["current_inventory"] == 500
    assert result["recommended_order_qty"] == 0  # no order needed


def test_restock_clamps_negative_qty(client, db):
    product = create_product(client)
    pid = product["id"]

    # 1000 units in stock
    client.post(
        "/api/inventory/events",
        json={
            "product_id": pid,
            "event_type": "PURCHASE",
            "quantity": 1000,
            "event_id": "evt-test-clamp",
        },
    )

    # projected demand = 15 * 7 = 105 total
    # safety stock = 105 * 0.20 = 21
    # without clamp: 105 + 21 - 1000 = -874
    # with clamp: max(0, -874) = 0
    mock_forecast_df = pd.DataFrame(
        {
            "ds": pd.date_range("2026-04-01", periods=7),
            "yhat": [15.0] * 7,
            "yhat_lower": [10.0] * 7,
            "yhat_upper": [20.0] * 7,
        }
    )

    with patch("app.services.restock_service.forecast", return_value=mock_forecast_df):
        result = get_restock_recommendation(db, pid)

    # this is the core assertion — qty must never be negative
    assert result["recommended_order_qty"] >= 0
    assert result["recommended_order_qty"] == 0


_FEATURE_FILE = os.path.join(
    os.path.dirname(__file__), "..", "feature_store", "daily_sales.parquet"
)
_MODEL_FILE_8 = os.path.join(os.path.dirname(__file__), "..", "models", "prophet_8.pkl")

_FEATURE_SKIP_REASON = "feature store not built — run make features"


@pytest.mark.skipif(not os.path.exists(_FEATURE_FILE), reason=_FEATURE_SKIP_REASON)
def test_feature_columns():
    df = pd.read_parquet(_FEATURE_FILE)
    expected = {
        "product_id",
        "date",
        "units_sold",
        "units_purchased",
        "net_delta",
        "rolling_avg_7d",
    }
    assert set(df.columns) == expected


@pytest.mark.skipif(not os.path.exists(_MODEL_FILE_8), reason="models not trained — run make train")
def test_forecast_returns_n_days():
    df = forecast(8, days=7)
    assert len(df) == 7


@pytest.mark.skipif(not os.path.exists(_FEATURE_FILE), reason=_FEATURE_SKIP_REASON)
def test_train_model_registers_to_mlflow(tmp_path, monkeypatch):
    pytest.importorskip("mlflow", reason="run `make train-deps` to install training dependencies")

    import app.services.forecast_service as forecast_service

    # Isolated model dir + registry so this test doesn't touch the real
    # models/ or mlflow.db, and doesn't collide with runs from `make train`.
    monkeypatch.setattr(forecast_service, "MODELS_DIR", tmp_path)
    monkeypatch.setattr(
        forecast_service, "MLFLOW_TRACKING_URI", f"sqlite:///{tmp_path / 'mlflow.db'}"
    )
    monkeypatch.chdir(tmp_path)  # artifact store defaults to ./mlruns relative to cwd

    result = forecast_service.train_model(1)

    assert (tmp_path / "prophet_1.pkl").exists()
    assert result["mlflow_model_version"] == 1
    assert result["mae_in_sample"] >= 0

    import mlflow

    client = mlflow.MlflowClient()
    versions = client.search_model_versions("name='prophet_1'")
    assert len(versions) == 1
    assert versions[0].run_id == result["mlflow_run_id"]


def test_forecast_endpoint_no_model(client):
    response = client.get("/api/forecast/99999")
    assert response.status_code == 404


@pytest.mark.parametrize("days", [0, -1, 91, 10_000])
def test_forecast_endpoint_rejects_out_of_range_days(client, days):
    response = client.get(f"/api/forecast/99999?days={days}")
    assert response.status_code == 422


def test_restock_endpoint_nonexistent_product(client):
    response = client.get("/api/forecast/restock/99999")
    assert response.status_code == 404


def test_restock_recommendation_nonexistent_product(db):
    with pytest.raises(Exception) as exc_info:
        get_restock_recommendation(db, 99999)
    assert getattr(exc_info.value, "status_code", None) == 404
