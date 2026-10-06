"""add_exercise_fields_to_homework_submissions

Revision ID: d3a2b1c4e5f6
Revises: e7f2b1a9c8d3
Create Date: 2026-10-06 14:35:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d3a2b1c4e5f6"
down_revision: str | Sequence[str] | None = "e7f2b1a9c8d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "homework_submissions",
        sa.Column("exercise_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "homework_submissions",
        sa.Column("exercise_title", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "homework_submissions",
        sa.Column("score", sa.Float(), nullable=True),
    )
    op.add_column(
        "homework_submissions",
        sa.Column("attempt_number", sa.Integer(), server_default="1", nullable=False),
    )

    op.create_index(
        "ix_homework_submissions_exercise_id",
        "homework_submissions",
        ["exercise_id"],
    )
    op.create_index(
        "ix_hw_submissions_lookup",
        "homework_submissions",
        ["homework_id", "user_id", "exercise_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_hw_submissions_lookup", table_name="homework_submissions")
    op.drop_index(
        "ix_homework_submissions_exercise_id", table_name="homework_submissions"
    )
    op.drop_column("homework_submissions", "attempt_number")
    op.drop_column("homework_submissions", "score")
    op.drop_column("homework_submissions", "exercise_title")
    op.drop_column("homework_submissions", "exercise_id")
