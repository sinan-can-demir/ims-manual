# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api.products import router as products_router
from app.api.inventory import router as inventory_router
from app.api.forecast import router as forecast_router

app = FastAPI()

_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(forecast_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}