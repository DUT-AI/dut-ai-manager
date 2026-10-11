"""create_meeting_overall_evaluations_table

Revision ID: b7c8d9e0f1a2
Revises: a8f1b2c3d4e5
Create Date: 2026-10-11 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7c8d9e0f1a2"
down_revision: str | Sequence[str] | None = "a8f1b2c3d4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_tables = insp.get_table_names()

    if "meeting_overall_evaluations" not in existing_tables:
        op.create_table(
            "meeting_overall_evaluations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("meeting_id", sa.Integer(), nullable=False),
            sa.Column("trainer_id", sa.Integer(), nullable=False),
            sa.Column(
                "scores",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
            ),
            sa.Column("average_score", sa.Float(), nullable=False),
            sa.Column("general_feedback", sa.String(length=2000), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column(
                "is_deleted",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.ForeignKeyConstraint(
                ["meeting_id"], ["meetings.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(["trainer_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "meeting_id",
                name="uq_meeting_overall_evaluation",
            ),
        )
        op.create_index(
            op.f("ix_meeting_overall_evaluations_meeting_id"),
            "meeting_overall_evaluations",
            ["meeting_id"],
            unique=True,
        )
        op.create_index(
            op.f("ix_meeting_overall_evaluations_trainer_id"),
            "meeting_overall_evaluations",
            ["trainer_id"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_meeting_overall_evaluations_trainer_id"),
        table_name="meeting_overall_evaluations",
    )
    op.drop_index(
        op.f("ix_meeting_overall_evaluations_meeting_id"),
        table_name="meeting_overall_evaluations",
    )
    op.drop_table("meeting_overall_evaluations")
