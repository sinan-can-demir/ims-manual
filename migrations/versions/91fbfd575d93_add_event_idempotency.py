"""add event idempotency

Revision ID: 91fbfd575d93
Revises: a7bb0a54ab00
Create Date: 2026-03-17 09:24:59.201223

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91fbfd575d93'
down_revision: Union[str, Sequence[str], None] = 'a7bb0a54ab00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add column as nullable FIRST
    op.add_column(
        'inventory_events',
        sa.Column('event_id', sa.String(), nullable=True)
    )

    # 2. Backfill existing rows with unique values
    op.execute("""
        UPDATE inventory_events
        SET event_id = CONCAT('backfill_', id)
    """)

    # 3. Make it NOT NULL
    op.alter_column(
        'inventory_events',
        'event_id',
        nullable=False
    )

    # 4. Add unique constraint (WITH NAME!)
    op.create_unique_constraint(
        'uq_inventory_events_event_id',
        'inventory_events',
        ['event_id']
    )

def downgrade() -> None:
    op.drop_constraint(
        'uq_inventory_events_event_id',
        'inventory_events',
        type_='unique'
    )

    op.drop_column('inventory_events', 'event_id')
