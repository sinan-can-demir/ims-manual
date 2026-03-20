from sqlalchemy.orm import Session
from app.schemas.product import ProductCreate
from app.models.product import Product
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

def create_product(db: Session, product: ProductCreate) -> Product:
    new_product = Product(
        name=product.name,
        sku=product.sku
    )

    try:
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return new_product

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Product with this SKU already exists"
        )