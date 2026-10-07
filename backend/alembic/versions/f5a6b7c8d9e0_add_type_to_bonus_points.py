"""add_type_to_bonus_points

Revision ID: f5a6b7c8d9e0
Revises: d3a2b1c4e5f6
Create Date: 2026-10-07 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f5a6b7c8d9e0"
down_revision: str | Sequence[str] | None = "e8d7c6b5a4f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns("bonus_points")]

    if "type" not in cols:
        op.add_column(
            "bonus_points",
            sa.Column("type", sa.String(length=50), nullable=True),
        )
        op.create_index(
            op.f("ix_bonus_points_type"), "bonus_points", ["type"], unique=False
        )

    # Backfill classification for existing rows based on reason
    op.execute(
        """
        UPDATE bonus_points 
        SET type = 'CLUB_ACTIVITY' 
        WHERE (reason ILIKE '%hoạt động tại clb%' OR reason ILIKE '%clb%' OR reason ILIKE '%lab%' OR reason ILIKE '%rèn luyện%');
        """
    )
    op.execute(
        """
        UPDATE bonus_points 
        SET type = 'OTHER' 
        WHERE type IS NULL OR type = '' OR type != 'CLUB_ACTIVITY';
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_bonus_points_type"), table_name="bonus_points")
    op.drop_column("bonus_points", "type")
