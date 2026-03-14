from app.models.product import Product
from app.services.product_service import create_product
from app.schemas.product import ProductCreate
from app.database import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

router = APIRouter()


@router.post("/products")
def create_product_route(product: ProductCreate, db: Session = Depends(get_db)):

    return create_product(db, Product(**product.model_dump()))
