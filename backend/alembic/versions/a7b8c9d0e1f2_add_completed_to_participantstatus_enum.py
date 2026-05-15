"""add completed to participantstatus enum

Revision ID: a7b8c9d0e1f2
Revises: 7300809d581f
Create Date: 2026-05-15 17:13:50.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = '7300809d581f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new enum value - must be outside transaction for PostgreSQL
    op.execute("COMMIT")
    op.execute("ALTER TYPE participantstatus ADD VALUE IF NOT EXISTS 'COMPLETED'")


def downgrade() -> None:
    """Downgrade schema."""
    # PostgreSQL doesn't support removing enum values directly
    pass
