"""add ALWAYS_TRIGGER to alerttype enum

Revision ID: 79c158abdb7a
Revises: af7c58b0156d
Create Date: 2026-04-11 17:53:11.997923

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '79c158abdb7a'
down_revision: Union[str, Sequence[str], None] = 'af7c58b0156d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE alerttype ADD VALUE 'ALWAYS_TRIGGER'")
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
