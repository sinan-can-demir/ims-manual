from app.services.product_service import create_product
from app.schemas.product import ProductCreate, ProductResponse
from app.database import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

router = APIRouter()


@router.post("/products", response_model=ProductResponse, status_code=201)
def create_product_route(product: ProductCreate, db: Session = Depends(get_db)):
    """
    Creates a new product with the given name and SKU.
    Returns the created product.
    status_code=201 indicates that a new resource has been created successfully.
    If a product with the same SKU already exists, returns 409 Conflict.
    """
    return create_product(db, product)
