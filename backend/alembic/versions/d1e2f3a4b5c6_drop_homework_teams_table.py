"""drop homework_teams table

Revision ID: d1e2f3a4b5c6
Revises: 02205cd879ae
Create Date: 2026-09-25 15:25:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: str | Sequence[str] | None = "02205cd879ae"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop homework_teams table."""
    op.execute("DROP TABLE IF EXISTS homework_teams CASCADE;")


def downgrade() -> None:
    """Recreate homework_teams table."""
    op.create_table(
        "homework_teams",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column(
            "homework_id",
            sa.Integer(),
            sa.ForeignKey("homeworks.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column(
            "team_id",
            sa.Integer(),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), default=False, nullable=True),
    )
