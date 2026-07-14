# app/main.py

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.forecast import router as forecast_router
from app.api.inventory import router as inventory_router
from app.api.products import router as products_router
from app.core.auth import require_api_key
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("API_KEY") is None:
        logger.warning("AUTH DISABLED — API_KEY not set; all endpoints are unauthenticated")
    yield


app = FastAPI(lifespan=lifespan)

_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

_auth = [Depends(require_api_key)]

app.include_router(products_router, prefix="/api", dependencies=_auth)
app.include_router(inventory_router, prefix="/api", dependencies=_auth)
app.include_router(forecast_router, prefix="/api", dependencies=_auth)


@app.get("/health")
def health():
    return {"status": "ok"}
