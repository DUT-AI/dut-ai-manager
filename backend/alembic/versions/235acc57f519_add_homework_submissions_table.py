"""add_homework_submissions_table

Revision ID: 235acc57f519
Revises: 6a13dfe16856
Create Date: 2026-10-05 00:30:31.591303

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '235acc57f519'
down_revision: Union[str, Sequence[str], None] = '6a13dfe16856'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "homework_submissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("homework_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("submission_type", sa.String(length=20), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_passed", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("details", sa.JSON(), server_default="{}", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["homework_id"], ["homeworks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_hw_submissions_lookup",
        "homework_submissions",
        ["homework_id", "user_id", "submission_type", "submitted_at"],
        unique=False,
    )
    op.create_index(op.f("ix_homework_submissions_homework_id"), "homework_submissions", ["homework_id"], unique=False)
    op.create_index(op.f("ix_homework_submissions_user_id"), "homework_submissions", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_homework_submissions_user_id"), table_name="homework_submissions")
    op.drop_index(op.f("ix_homework_submissions_homework_id"), table_name="homework_submissions")
    op.drop_index("idx_hw_submissions_lookup", table_name="homework_submissions")
    op.drop_table("homework_submissions")
