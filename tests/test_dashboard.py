# tests/test_dashboard.py

import os

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from .utils import create_product, purchase

_FEATURE_FILE = os.path.join(
    os.path.dirname(__file__), "..", "feature_store", "daily_sales.parquet"
)
_FEATURE_SKIP_REASON = "feature store not built — run make features"


def _fake_forecast_df():
    return pd.DataFrame(
        {
            "ds": pd.date_range("2026-04-01", periods=7),
            "yhat": [15.0] * 7,
            "yhat_lower": [10.0] * 7,
            "yhat_upper": [20.0] * 7,
        }
    )


@pytest.mark.skipif(not os.path.exists(_FEATURE_FILE), reason=_FEATURE_SKIP_REASON)
def test_dashboard_renders_without_exception(client, dashboard_db, monkeypatch):
    product = create_product(client)
    purchase(client, product["id"], 50)

    monkeypatch.setattr("dashboard.data.forecast", lambda *a, **k: _fake_forecast_df())

    at = AppTest.from_file("dashboard/app.py")
    at.run()

    assert not at.exception


@pytest.mark.skipif(not os.path.exists(_FEATURE_FILE), reason=_FEATURE_SKIP_REASON)
def test_dashboard_shows_inventory_metric(client, dashboard_db, monkeypatch):
    product = create_product(client)
    purchase(client, product["id"], 50)

    monkeypatch.setattr("dashboard.data.forecast", lambda *a, **k: _fake_forecast_df())

    at = AppTest.from_file("dashboard/app.py")
    at.run()

    assert not at.exception
    metric_labels = [m.label for m in at.metric]
    assert "Current Inventory" in metric_labels
