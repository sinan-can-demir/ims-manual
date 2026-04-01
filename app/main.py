# app/main.py

from fastapi import FastAPI
from app.api.products import router as products_router
from app.api.inventory import router as inventory_router
from app.api.forecast import router as forecast_router

app = FastAPI()

app.include_router(products_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(forecast_router, prefix="/api")