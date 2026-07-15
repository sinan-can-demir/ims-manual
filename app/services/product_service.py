from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateSKUError
from app.core.logging import logger
from app.models.product import Product
from app.schemas.product import ProductCreate


def create_product(db: Session, product: ProductCreate) -> Product:
    new_product = Product(name=product.name, sku=product.sku)

    try:
        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        logger.info("product_created", extra={"product_id": new_product.id, "sku": product.sku})

        return new_product

    except IntegrityError:
        db.rollback()
        raise DuplicateSKUError(product.sku)
