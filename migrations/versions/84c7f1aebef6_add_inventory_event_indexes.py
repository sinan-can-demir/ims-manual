"""add inventory event indexes

Revision ID: 84c7f1aebef6
Revises: d6e00aa295e6
Create Date: 2026-03-16 19:02:45.818247

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84c7f1aebef6'
down_revision: Union[str, Sequence[str], None] = 'd6e00aa295e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op

def upgrade():

    op.create_index(
        "ix_inventory_events_product_id",
        "inventory_events",
        ["product_id"]
    )

    op.create_index(
        "ix_inventory_events_created_at",
        "inventory_events",
        ["created_at"]
    )

    op.create_index(
        "ix_inventory_events_product_created",
        "inventory_events",
        ["product_id", "created_at"]
    )


def downgrade():

    op.drop_index("ix_inventory_events_product_created", table_name="inventory_events")
    op.drop_index("ix_inventory_events_created_at", table_name="inventory_events")
    op.drop_index("ix_inventory_events_product_id", table_name="inventory_events")