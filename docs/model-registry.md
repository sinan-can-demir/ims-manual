# Model Registry (MLflow)

`make train` logs every Prophet training run to a local MLflow model
registry — training metrics, model params, and the model artifact itself,
versioned per product (registered model name: `prophet_{product_id}`).

This is separate from model *serving*: the API still loads
`models/prophet_{product_id}.pkl` directly (see `forecast_service.load_model`),
unchanged. The registry is a record of what was trained, when, and how it
scored — useful for comparing runs and knowing what to roll back to; it
doesn't sit in the request path.

## Setup

Training dependencies aren't part of `requirements.txt` (and therefore not
part of the API Docker image) — they're only needed on whatever machine
runs `make train`:

```bash
make train-deps   # pip install -r requirements-train.txt
make train
```

By default the registry is backed by a local SQLite file at `mlflow.db`
(repo root), with artifacts under `mlruns/`. Both are gitignored — override
with `MLFLOW_TRACKING_URI` / `MLFLOW_EXPERIMENT_NAME` env vars if you want a
shared registry (e.g. a `postgresql://` URI) instead.

MLflow's plain filesystem tracking store (`file:./mlruns` with no database)
is in maintenance mode and doesn't support the model registry — that's why
SQLite is the default here, not a bare directory.

## Viewing runs

`mlflow-skinny` (what `requirements-train.txt` installs) is the tracking/registry
client only — it doesn't bundle the web UI. Two options:

**Python client** (works with `mlflow-skinny`, no extra install):

```python
import mlflow
mlflow.set_tracking_uri("sqlite:///mlflow.db")
client = mlflow.MlflowClient()
for v in client.search_model_versions("name='prophet_1'"):
    print(v.version, v.aliases, v.creation_timestamp)
```

**Web UI** (needs the full `mlflow` package, not `mlflow-skinny`):

```bash
pip install mlflow
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Then open `http://localhost:5000`.

## Promotion and rollback

MLflow's model *stages* API (Staging/Production) is deprecated in favor of
**aliases** — arbitrary named pointers to a specific version. This project
uses `champion` as the alias for "the version restock/forecast decisions
should be based on" (a convention, not something the API reads — see
Serving above).

Promote a version to champion:

```python
import mlflow
mlflow.set_tracking_uri("sqlite:///mlflow.db")
client = mlflow.MlflowClient()
client.set_registered_model_alias("prophet_1", "champion", version=3)
```

Roll back — same call, pointed at the previous version:

```python
client.set_registered_model_alias("prophet_1", "champion", version=2)
```

Load whichever version is currently `champion`:

```python
import mlflow.prophet
model = mlflow.prophet.load_model("models:/prophet_1@champion")
```

Promoting a `champion` alias doesn't change what the API serves — that's
still `models/prophet_{product_id}.pkl`, written by every `make train` run
regardless of registry state. To actually roll back what's serving, restore
the `.pkl` for the version you want (via `mlflow artifacts download` against
that run, or by re-running training against older feature data) and copy it
into `models/`.
