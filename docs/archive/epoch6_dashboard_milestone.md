# IMS Milestone — Epoch 6 — Application Layer (Dashboard)

## Date: 2026-04-01
## Focus: Build an Inventory Dashboard with Streamlit

---

## 🎯 Goal

Build a professional, interactive dashboard that surfaces everything
your system knows — current inventory, demand forecasts, restock
alerts, and event history — in a single interface a warehouse manager
could actually use.

This epoch teaches you:
- How frontend applications are structured (layout, state, data flow)
- How to connect a UI to a backend service layer
- How to present data visually (charts, tables, metrics, alerts)
- Core frontend concepts that transfer to React or Vue later

---

## 🧠 Why Streamlit

Streamlit lets you build a real, interactive web application in pure
Python. No HTML, no CSS, no JavaScript required to get started.

This is the right tool for this epoch because:
- You already know Python — you write UI the same way you write scripts
- It connects directly to your existing services and DataFrames
- It produces genuinely professional-looking dashboards
- The concepts you learn (layout, state, reactivity) transfer to any
  frontend framework later
- It is actively used in production at data and ML teams

**What Streamlit actually is:**

Every time a user interacts with a Streamlit app (selects a dropdown,
clicks a button), the entire Python script re-runs from top to bottom.
Streamlit figures out what changed and updates only that part of the UI.

This is the core mental model:

```
User interaction
      ↓
Script re-runs top to bottom
      ↓
Streamlit diffs the output
      ↓
UI updates
```

Once this clicks, everything else follows naturally.

---

## 🧠 Frontend Concepts You Will Learn

| Concept | Streamlit equivalent | React equivalent (later) |
|---|---|---|
| Layout | `st.columns()`, `st.sidebar` | CSS Grid, Flexbox |
| State | `st.session_state` | `useState` |
| Reactivity | Script re-runs on interaction | Component re-renders |
| Data binding | Pass DataFrame to chart | Props |
| Conditional rendering | `if/else` in Python | Conditional JSX |
| User input | `st.selectbox()`, `st.button()` | `<select>`, `<button>` |

---

## 🏗️ Target Dashboard Layout

```
┌──────────────────────────────────────────────────────┐
│  🏭 IMS — Inventory Management Dashboard             │
├──────────────────────────────────────────────────────┤
│  Sidebar:                                            │
│  [Product selector dropdown]                         │
│  [Refresh button]                                    │
├────────────────────┬─────────────────────────────────┤
│  Current Stock     │  Restock Alert                  │
│  📦 44 units       │  ⚠️ URGENT — Order 118 units    │
├────────────────────┴─────────────────────────────────┤
│  7-Day Demand Forecast                               │
│  [Line chart with confidence band]                   │
├──────────────────────────────────────────────────────┤
│  Recent Inventory Events                             │
│  [Table: date, event_type, quantity, event_id]       │
└──────────────────────────────────────────────────────┘
```

---

## 🏗️ Tasks

---

### BLOCK 1 — Setup (30 min)

- [x] Install Streamlit:
  ```bash
  pip install streamlit
  ```
- [x] Add `streamlit` to `requirements.txt`
- [x] Create `dashboard/` directory at project root
- [x] Create `dashboard/app.py` — this is your entire frontend

**Why a separate directory:**
The dashboard is a separate application that sits on top of your
backend services. Keeping it in its own directory makes the boundary
clear — `app/` is the backend, `dashboard/` is the frontend.

- [x] Add a Makefile target:
  ```makefile
  dashboard:
      streamlit run dashboard/app.py
  ```
- [x] Verify Streamlit works:
  ```bash
  make dashboard
  ```
  A browser tab should open automatically at `http://localhost:8501`

**Commit:**
```bash
git commit -m "chore(dashboard): add streamlit and dashboard directory"
```

---

### BLOCK 2 — Product Selector and Basic Layout (45 min)

**File:** `dashboard/app.py`

This block teaches you the fundamental Streamlit pattern: sidebar for
controls, main area for content.

```python
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add project root to path so we can import app services
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.services.inventory_service import get_inventory
from app.api.inventory import get_product_events

# --- Page config (must be first Streamlit call) ---
st.set_page_config(
    page_title="IMS Dashboard",
    page_icon="🏭",
    layout="wide"
)

st.title("🏭 Inventory Management Dashboard")

# --- Sidebar ---
st.sidebar.header("Controls")

# Load products for the dropdown
# We read directly from the feature store to get product IDs
# In a larger app this would be a dedicated API call
feature_df = pd.read_parquet("feature_store/daily_sales.parquet")
product_ids = sorted(feature_df["product_id"].unique().tolist())

selected_product = st.sidebar.selectbox(
    "Select Product",
    options=product_ids,
    format_func=lambda pid: f"Product {pid}"
)

st.sidebar.button("🔄 Refresh")
```

#### Key concept: `st.sidebar`

The sidebar is a persistent panel on the left side of the screen.
It's the right place for controls that apply to the whole page —
product selector, filters, refresh button. The main area is for
content that changes based on those controls.

#### Key concept: `selectbox`

`st.selectbox()` renders a dropdown and returns the selected value.
When the user changes the selection, Streamlit re-runs the script and
`selected_product` has the new value. This is reactivity in action —
you don't write any event listeners, you just use the return value.

- [ ] Write the page config and sidebar
- [ ] Display `st.write(f"Selected product: {selected_product}")` as a
  placeholder to verify the dropdown works
- [ ] Run `make dashboard` and test the dropdown

**Commit:**
```bash
git commit -m "feat(dashboard): add product selector and sidebar layout"
```

---

### BLOCK 3 — Inventory Metrics and Restock Alert (45 min)

This block teaches you `st.columns()` for side-by-side layout and
`st.metric()` for KPI displays.

```python
from app.services.restock_service import get_restock_recommendation
from app.services.forecast_service import forecast

# --- Database session ---
# Open a session for this script run
db = SessionLocal()

try:
    # Fetch data for selected product
    current_qty = get_inventory(db, selected_product)
    restock = get_restock_recommendation(db, selected_product)
finally:
    db.close()

# --- Metrics row ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Current Inventory",
        value=f"{current_qty} units",
    )

with col2:
    st.metric(
        label="Projected Demand (7d)",
        value=f"{restock['projected_demand_7d']} units",
    )

with col3:
    st.metric(
        label="Recommended Order",
        value=f"{restock['recommended_order_qty']} units",
    )

# --- Restock alert ---
urgency = restock["urgency"]

urgency_config = {
    "STOCKOUT": ("🔴", "error"),
    "URGENT":   ("🟠", "warning"),
    "LOW":      ("🟡", "warning"),
    "OK":       ("🟢", "success"),
}

icon, alert_type = urgency_config[urgency]

if alert_type == "error":
    st.error(f"{icon} {urgency} — Restock immediately! "
             f"Order {restock['recommended_order_qty']} units.")
elif alert_type == "warning":
    st.warning(f"{icon} {urgency} — "
               f"{restock['days_of_stock_remaining']} days of stock remaining. "
               f"Order {restock['recommended_order_qty']} units.")
else:
    st.success(f"{icon} Stock levels are healthy.")
```

#### Key concept: `st.columns()`

`st.columns(3)` splits the page into 3 equal columns. You use `with
col1:` to place content inside each one. This is how you build
side-by-side layouts without writing any CSS.

#### Key concept: `st.metric()`

`st.metric()` renders a KPI card — a label, a large value, and an
optional delta (change indicator). It's the standard way to show
key numbers in a dashboard.

#### Key concept: conditional alerts

`st.error()`, `st.warning()`, and `st.success()` render colored alert
banners. Using the urgency classification from your restock service
to drive which one appears is the right pattern — the UI reflects
the business logic without duplicating it.

- [ ] Add metrics row with current inventory, projected demand, recommended order
- [ ] Add urgency alert that changes color based on restock status
- [ ] Test with different products — alert should change per product

**Commit:**
```bash
git commit -m "feat(dashboard): add inventory metrics and restock alert"
```

---

### BLOCK 4 — Forecast Chart (1 hour)

This block teaches you data visualization — the most important frontend
skill for a data engineer.

```python
import plotly.graph_objects as go

# --- Forecast chart ---
st.subheader("7-Day Demand Forecast")

try:
    forecast_df = forecast(selected_product, days=7)

    fig = go.Figure()

    # Confidence band (shaded area between lower and upper bounds)
    fig.add_trace(go.Scatter(
        x=pd.concat([forecast_df["ds"], forecast_df["ds"][::-1]]),
        y=pd.concat([forecast_df["yhat_upper"], forecast_df["yhat_lower"][::-1]]),
        fill="toself",
        fillcolor="rgba(99, 102, 241, 0.15)",
        line=dict(color="rgba(255,255,255,0)"),
        name="Confidence interval",
        showlegend=True
    ))

    # Predicted demand line
    fig.add_trace(go.Scatter(
        x=forecast_df["ds"],
        y=forecast_df["yhat"].clip(lower=0),
        mode="lines+markers",
        line=dict(color="#6366f1", width=2),
        marker=dict(size=6),
        name="Predicted demand"
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
```

#### Key concept: Plotly for charts

Streamlit works with several charting libraries. Plotly is the best
choice for production dashboards because it produces interactive charts
— users can hover, zoom, and pan. `st.plotly_chart()` renders it
directly in the page.

#### Key concept: confidence band

The shaded area between `yhat_lower` and `yhat_upper` is the
uncertainty range. Showing it alongside the point prediction is
the correct way to present a probabilistic forecast — it communicates
that the model is not certain, which is honest and important.

#### Key concept: graceful degradation

The `try/except FileNotFoundError` block means the dashboard still
works even if no model has been trained for a product. It shows an
informative message instead of crashing. Always handle the case where
data isn't available yet.

- [ ] Install plotly: `pip install plotly`
- [ ] Add `plotly` to `requirements.txt`
- [ ] Build the forecast chart with confidence band
- [ ] Test with products that have trained models and products that don't

**Commit:**
```bash
git commit -m "feat(dashboard): add forecast chart with confidence band"
```

---

### BLOCK 5 — Event History Table (30 min)

The event log is the source of truth for your entire system. Surfacing
it in the dashboard gives operators full visibility into what happened.

```python
from sqlalchemy.orm import Session
from app.models.inventory_event import InventoryEvent

# --- Event history ---
st.subheader("Recent Inventory Events")

db = SessionLocal()
try:
    events = (
        db.query(InventoryEvent)
        .filter(InventoryEvent.product_id == selected_product)
        .order_by(InventoryEvent.created_at.desc())
        .limit(20)
        .all()
    )
finally:
    db.close()

if events:
    events_df = pd.DataFrame([{
        "Date":       e.created_at.strftime("%Y-%m-%d %H:%M"),
        "Event Type": e.event_type.value,
        "Quantity":   e.quantity,
        "Event ID":   e.event_id,
    } for e in events])

    st.dataframe(events_df, use_container_width=True, hide_index=True)
else:
    st.info("No events recorded for this product yet.")
```

#### Key concept: `st.dataframe()`

`st.dataframe()` renders an interactive table. Users can sort columns
by clicking headers and scroll horizontally. `hide_index=True` removes
the pandas row numbers which look unprofessional in a UI.

#### Key concept: formatting before display

Notice how we build a clean dictionary with human-readable keys
("Event Type" not "event_type") and formatted dates before passing
to the DataFrame. Always format data for humans before displaying it —
raw database fields with underscores and UTC timestamps are not what
users want to see.

- [ ] Add event history table with last 20 events for selected product
- [ ] Format columns for readability
- [ ] Test switching products — table should update

**Commit:**
```bash
git commit -m "feat(dashboard): add event history table"
```

---

### BLOCK 6 — Polish and UX Details (30 min)

The difference between a prototype and a professional dashboard is
attention to the details that make it usable.

#### Loading states

Slow operations should show a spinner:

```python
with st.spinner("Loading forecast..."):
    forecast_df = forecast(selected_product, days=7)
```

#### Caching

Right now every product selection re-fetches everything from scratch.
For slow operations, cache the result:

```python
@st.cache_data(ttl=300)  # cache for 5 minutes
def load_forecast(product_id: int):
    return forecast(product_id, days=7)
```

`ttl=300` means the cache expires after 5 minutes — after that
Streamlit re-runs the function and gets fresh data. This is the
standard pattern for dashboards that show near-real-time data.

#### Page sections with dividers

```python
st.divider()  # horizontal rule between sections
```

#### Empty states

Always handle the case where there's no data:

```python
if not events:
    st.info("No events recorded for this product yet.")
```

- [ ] Add `st.spinner()` around slow operations
- [ ] Add `@st.cache_data` to forecast and restock calls
- [ ] Add `st.divider()` between sections
- [ ] Handle empty states for all data fetches
- [ ] Test the full dashboard end to end

**Commit:**
```bash
git commit -m "feat(dashboard): add caching, spinners, and polish"
```

---

### BLOCK 7 — Documentation and Roadmap (15 min)

- [ ] Update `ROADMAP.md` — mark Epoch 6 complete
- [ ] Update `README.md` — add dashboard section:
  ```
  make dashboard   → start the Streamlit dashboard at localhost:8501
  ```
- [ ] Update `Last Updated` date

**Commit:**
```bash
git commit -m "docs: mark Epoch 6 complete and update roadmap"
```

---

## 🧪 Definition of Done

Epoch 6 is complete when:

- [ ] `make dashboard` starts the app at `http://localhost:8501`
- [ ] Product selector changes all content on the page
- [ ] Current inventory, projected demand, recommended order all display
- [ ] Restock alert changes color based on urgency
- [ ] Forecast chart shows with confidence band
- [ ] Event history table shows last 20 events
- [ ] No crashes when switching between products
- [ ] Graceful message when no model exists for a product

---

## 📋 Suggested Commit Order

```
chore(dashboard): add streamlit and dashboard directory
feat(dashboard): add product selector and sidebar layout
feat(dashboard): add inventory metrics and restock alert
feat(dashboard): add forecast chart with confidence band
feat(dashboard): add event history table
feat(dashboard): add caching, spinners, and polish
docs: mark Epoch 6 complete and update roadmap
```

---

## ⚠️ Things to Watch Out For

**Database sessions in Streamlit.**
Because the script re-runs on every interaction, you must open and
close the database session within each run. Never store a SQLAlchemy
session in `st.session_state` — sessions are not thread-safe across
re-runs. Always use try/finally to ensure the session closes.

**`st.set_page_config()` must be the first Streamlit call.**
If you call any other `st.*` function before it, Streamlit will throw
an error. Put it at the very top of the script, right after imports.

**`sys.path.insert()` for local imports.**
Because `dashboard/app.py` is outside the `app/` package, you need
to add the project root to the Python path so imports like
`from app.services.forecast_service import forecast` resolve correctly.

**Plotly is a separate install.**
`pip install plotly` and add it to `requirements.txt`. Streamlit does
not bundle it.

**The dashboard reads from the live database.**
Make sure Docker is running (`make up-d`) before starting the
dashboard, otherwise database calls will fail.

---

## 🧠 What You Will Learn

By the end of this epoch you will understand:

- How a frontend application is structured (layout, controls, content)
- How state and reactivity work (why the script re-runs)
- How to present data visually (charts, tables, metrics)
- How to connect a UI to a backend service layer
- How to handle loading, errors, and empty states gracefully
- The difference between a prototype and a polished product

These concepts transfer directly to React, Vue, or any other frontend
framework. The tools change, the ideas don't.

---

## 🚀 Next Milestone Preview

Once Epoch 6 is complete you have a full-stack system:

```
PostgreSQL → Event log → Data lake → Warehouse → ML layer → Dashboard
```

The natural next directions are:

- **Epoch 7 — Kafka streaming** — real-time event processing as an
  alternative write path (data engineering track)
- **Epoch 8 — Advanced ML** — model retraining pipeline, feature
  importance, model versioning (ML engineering track)
- **Deploy** — put this on a real server so you can share the URL
  in interviews (cloud/DevOps track)
