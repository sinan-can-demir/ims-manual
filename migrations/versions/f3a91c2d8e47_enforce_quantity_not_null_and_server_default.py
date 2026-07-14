"""enforce quantity not null and server default

Revision ID: f3a91c2d8e47
Revises: a7bb0a54ab00
Create Date: 2026-06-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a91c2d8e47'
down_revision: Union[str, Sequence[str], None] = 'a7bb0a54ab00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fill any existing NULLs before adding the NOT NULL constraint
    op.execute("UPDATE inventory_events SET quantity = 0 WHERE quantity IS NULL")
    op.alter_column('inventory_events', 'quantity',
                    existing_type=sa.INTEGER(),
                    nullable=False)

    op.alter_column('inventory_state', 'quantity',
                    existing_type=sa.INTEGER(),
                    nullable=False,
                    server_default='0')


def downgrade() -> None:
    op.alter_column('inventory_state', 'quantity',
                    existing_type=sa.INTEGER(),
                    nullable=True,
                    server_default=None)

    op.alter_column('inventory_events', 'quantity',
                    existing_type=sa.INTEGER(),
                    nullable=True)
