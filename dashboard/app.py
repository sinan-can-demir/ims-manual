# dashboard/app.py

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Add project root to path so app imports resolve correctly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.inventory_event import InventoryEvent
from app.services.forecast_service import forecast
from app.services.inventory_service import get_inventory
from app.services.restock_service import get_restock_recommendation

# ---------------------------------------------------------------
# Page config — must be the first Streamlit call in the script
# ---------------------------------------------------------------
st.set_page_config(
    page_title="IMS Dashboard",
    page_icon="🏭",
    layout="wide"
)

# ---------------------------------------------------------------
# Data loaders
# Sessions stay outside the cache layer.
# Cache only plain Python values — never ORM objects.
# ---------------------------------------------------------------

def _get_inventory(product_id: int) -> int:
    db = SessionLocal()
    try:
        return get_inventory(db, product_id)
    finally:
        db.close()


def _get_restock(product_id: int) -> dict:
    db = SessionLocal()
    try:
        return get_restock_recommendation(db, product_id)
    finally:
        db.close()


def _get_events(product_id: int) -> list[dict]:
    db = SessionLocal()
    try:
        events = (
            db.query(InventoryEvent)
            .filter(InventoryEvent.product_id == product_id)
            .order_by(InventoryEvent.created_at.desc())
            .limit(20)
            .all()
        )
        # Serialize to plain dicts here, inside the session,
        # before the session closes. Never let ORM objects
        # escape the session boundary.
        return [{
            "Date":       e.created_at.strftime("%Y-%m-%d %H:%M"),
            "Event Type": e.event_type.value,
            "Quantity":   e.quantity,
            "Event ID":   e.event_id,
        } for e in events]
    finally:
        db.close()


@st.cache_data(ttl=300)
def load_inventory(product_id: int) -> int:
    return _get_inventory(product_id)


@st.cache_data(ttl=300)
def load_restock(product_id: int) -> dict:
    return _get_restock(product_id)


@st.cache_data(ttl=300)
def load_forecast(product_id: int) -> pd.DataFrame:
    return forecast(product_id, days=7)


@st.cache_data(ttl=300)
def load_events(product_id: int) -> list[dict]:
    return _get_events(product_id)


# ---------------------------------------------------------------
# Sidebar — controls
# ---------------------------------------------------------------
st.title("🏭 Inventory Management Dashboard")
st.sidebar.header("Controls")

feature_df = pd.read_parquet("feature_store/daily_sales.parquet")
product_ids = sorted(feature_df["product_id"].unique().tolist())

selected_product = st.sidebar.selectbox(
    "Select Product",
    options=product_ids,
    format_func=lambda pid: f"Product {pid}"
)

if st.sidebar.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

# ---------------------------------------------------------------
# Section 1 — Inventory metrics
# ---------------------------------------------------------------
current_qty = load_inventory(selected_product)
restock     = load_restock(selected_product)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Current Inventory", f"{current_qty} units")

with col2:
    st.metric("Projected Demand (7d)", f"{restock['projected_demand_7d']} units")

with col3:
    st.metric("Recommended Order", f"{restock['recommended_order_qty']} units")

# ---------------------------------------------------------------
# Section 2 — Restock alert
# ---------------------------------------------------------------
urgency_config = {
    "STOCKOUT": ("🔴", "error"),
    "URGENT":   ("🟠", "warning"),
    "LOW":      ("🟡", "warning"),
    "OK":       ("🟢", "success"),
}

icon, alert_type = urgency_config[restock["urgency"]]

if alert_type == "error":
    st.error(
        f"{icon} {restock['urgency']} — Restock immediately! "
        f"Order {restock['recommended_order_qty']} units."
    )
elif alert_type == "warning":
    st.warning(
        f"{icon} {restock['urgency']} — "
        f"{restock['days_of_stock_remaining']} days of stock remaining. "
        f"Order {restock['recommended_order_qty']} units."
    )
else:
    st.success(f"{icon} Stock levels are healthy.")

# ---------------------------------------------------------------
# Section 3 — Forecast chart
# ---------------------------------------------------------------
st.divider()
st.subheader("7-Day Demand Forecast")

try:
    with st.spinner("Loading forecast..."):
        forecast_df = load_forecast(selected_product)

    fig = go.Figure()

    # Shaded confidence band
    fig.add_trace(go.Scatter(
        x=pd.concat([forecast_df["ds"], forecast_df["ds"][::-1]]),
        y=pd.concat([forecast_df["yhat_upper"], forecast_df["yhat_lower"][::-1]]),
        fill="toself",
        fillcolor="rgba(99, 102, 241, 0.15)",
        line=dict(color="rgba(255,255,255,0)"),
        name="Confidence interval",
    ))

    # Predicted demand line
    fig.add_trace(go.Scatter(
        x=forecast_df["ds"],
        y=forecast_df["yhat"].clip(lower=0),
        mode="lines+markers",
        line=dict(color="#6366f1", width=2),
        marker=dict(size=6),
        name="Predicted demand",
    ))

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Units",
        hovermode="x unified",
        height=350,
        margin=dict(l=0, r=0, t=20, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)

except FileNotFoundError:
    st.info("⚠️ No trained model found for this product. Run make train first.")

# ---------------------------------------------------------------
# Section 4 — Event history table
# ---------------------------------------------------------------
st.divider()
st.subheader("Recent Inventory Events")

events = load_events(selected_product)

if events:
    st.dataframe(
        pd.DataFrame(events),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No events recorded for this product yet.")