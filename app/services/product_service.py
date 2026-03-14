from sqlalchemy.orm import Session
from app.schemas.product import ProductCreate
from app.models.product import Product


def create_product(db: Session, product_data: ProductCreate) -> Product:

    product = Product(name=product_data.name, sku=product_data.sku)

    db.add(product)

    db.commit()

    db.refresh(product)

    return product

