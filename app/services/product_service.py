from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.schemas.product import ProductCreate
from app.models.product import Product
from app.core.logging import logger

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

        logger.info(
            "product_created",
            extra={
                "product_id": new_product.id,
                "sku": product.sku
            }
        )
        
        return new_product

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Product with this SKU already exists"
        )