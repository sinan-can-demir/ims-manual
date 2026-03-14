from fastapi import FastAPI
from app.database import Base, engine
from app.models import product
from app.models import inventory_event
from app.api.products import router as products_router
from app.api.inventory import router as inventory_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(products_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")