# app/main.py

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.forecast import router as forecast_router
from app.api.inventory import router as inventory_router
from app.api.products import router as products_router
from app.api.webhooks import router as webhooks_router
from app.core.auth import require_api_key
from app.core.exceptions import DomainError
from app.core.logging import RequestLoggingMiddleware, logger
from app.core.metrics import MetricsMiddleware, metrics_response


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("API_KEY") is None:
        logger.warning("AUTH DISABLED — API_KEY not set; all endpoints are unauthenticated")
    if os.getenv("WEBHOOK_SECRET") is None:
        logger.warning(
            "WEBHOOK AUTH DISABLED — WEBHOOK_SECRET not set; /api/webhooks/ingest "
            "accepts unsigned requests"
        )
    yield


app = FastAPI(lifespan=lifespan)

_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(MetricsMiddleware)

_auth = [Depends(require_api_key)]

app.include_router(products_router, prefix="/api", dependencies=_auth)
app.include_router(inventory_router, prefix="/api", dependencies=_auth)
app.include_router(forecast_router, prefix="/api", dependencies=_auth)
# Signed with WEBHOOK_SECRET (see require_webhook_signature), not the
# X-API-Key used by the routers above — different trust boundary.
app.include_router(webhooks_router, prefix="/api")


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return metrics_response()
