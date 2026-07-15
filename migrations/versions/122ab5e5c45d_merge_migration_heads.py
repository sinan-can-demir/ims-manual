"""merge migration heads

Revision ID: 122ab5e5c45d
Revises: 91fbfd575d93, f3a91c2d8e47
Create Date: 2026-07-14 01:19:44.668512

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '122ab5e5c45d'
down_revision: Union[str, Sequence[str], None] = ('91fbfd575d93', 'f3a91c2d8e47')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
