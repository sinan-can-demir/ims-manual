# IMS --- Inventory Management System

A minimal event‑driven **Inventory Management System** designed to
evolve into a **data platform + ML pipeline**.

------------------------------------------------------------------------

# System Vision

The IMS platform will eventually support:

-   Inventory operations
-   Data pipelines
-   Analytics datasets
-   Demand forecasting models
-   ML monitoring

Architecture philosophy:

Events are the source of truth\
Schemas are contracts\
Pipelines must be reproducible\
ML depends on data quality

------------------------------------------------------------------------

# High Level Architecture

FastAPI Service (Inventory API) │ │ writes ▼ PostgreSQL
(inventory_events) │ │ batch export ▼ Data Lake (Parquet datasets) │ │
transformations ▼ Analytics Layer (daily sales) │ ▼ ML Pipeline
(forecasting)

------------------------------------------------------------------------

# Repository Structure

ims/

app/ main.py api/ services/ models/

db/ migrations/ schema.sql

pipelines/ export_events.py transform_sales.py

data_lake/

docker/ Dockerfile docker-compose.yml

scripts/

README.md ROADMAP.md

------------------------------------------------------------------------

# Development Epochs

Each epoch should produce a **working system**.

------------------------------------------------------------------------

# EPOCH 0 --- Foundations

Goal: Run the application locally.

Tech stack: - Docker - PostgreSQL - FastAPI - Python

Tasks:

-   Setup repository structure
-   Create docker-compose
-   Run PostgreSQL container
-   Create FastAPI app
-   Connect FastAPI to database
-   Environment configuration (.env)

Result:

docker compose up

should start: - API server - PostgreSQL

------------------------------------------------------------------------

# EPOCH 1 --- Core Inventory System

Key Idea:

Inventory is NOT stored.\
Inventory is computed from events.

------------------------------------------------------------------------

## Database Schema

### products

  column       type
  ------------ -----------
  id           serial
  name         text
  sku          text
  created_at   timestamp

### inventory_events

  column       type
  ------------ -----------
  id           serial
  product_id   int
  event_type   text
  quantity     int
  created_at   timestamp

Event types:

purchase\
sale\
adjustment\
return

Example:

  id   product_id   event_type   quantity
  ---- ------------ ------------ ----------
  1    1            purchase     50
  2    1            sale         -5

Inventory = SUM(quantity)

------------------------------------------------------------------------

## API Endpoints

Products

POST /products\
GET /products\
GET /products/{{id}}

Inventory

POST /inventory/purchase\
POST /inventory/sale\
GET /inventory/{{product_id}}

------------------------------------------------------------------------

# EPOCH 2 --- Data Export Pipeline

Pipeline:

PostgreSQL → Python Batch Job → Parquet Dataset

Example output:

data_lake/ inventory_events/ date=YYYY-MM-DD/ events.parquet

Tasks:

-   Create export_events.py
-   Read events from Postgres
-   Write Parquet files
-   Partition by date

------------------------------------------------------------------------

# EPOCH 3 --- Analytics Layer

Create aggregated datasets.

Example:

daily_sales

  date   product_id   units_sold
  ------ ------------ ------------

Generated from sales events grouped by product and date.

Output:

data_lake/analytics/daily_sales.parquet

------------------------------------------------------------------------

# EPOCH 4 --- ML Integration

Inputs for ML:

-   daily_sales
-   inventory_levels
-   product_metadata

Pipeline:

dataset → model training → prediction

Example prediction:

next_7_day_demand

------------------------------------------------------------------------

# Milestone 1

First working milestone:

FastAPI + PostgreSQL + inventory_events table

Working endpoints:

POST /purchase\
POST /sale\
GET /inventory/{{product}}

------------------------------------------------------------------------

# Long Term Vision

Inventory System ↓ Data Platform ↓ ML Pipeline ↓ Smart Inventory
Optimization

