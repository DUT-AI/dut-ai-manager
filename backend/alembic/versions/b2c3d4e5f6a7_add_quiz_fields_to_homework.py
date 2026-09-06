"""add quiz fields to homework

Revision ID: b2c3d4e5f6a7
Revises: b1c2d3e4f5a6
Create Date: 2026-08-31 21:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "b1c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("homeworks", sa.Column("link", sa.String(length=500), nullable=True))
    op.add_column("homeworks", sa.Column("game_slug", sa.String(length=255), nullable=True))
    op.add_column(
        "homeworks", sa.Column("homework_slug", sa.String(length=255), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("homeworks", "homework_slug")
    op.drop_column("homeworks", "game_slug")
    op.drop_column("homeworks", "link")
