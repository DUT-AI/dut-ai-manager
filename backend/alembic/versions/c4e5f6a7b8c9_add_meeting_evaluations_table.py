"""add_meeting_evaluations_and_enable_evaluation

Revision ID: c4e5f6a7b8c9
Revises: 4405c56add67
Create Date: 2026-10-02 10:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "e1a2b3c4d5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    meeting_cols = [c["name"] for c in insp.get_columns("meetings")]

    # 1. Add enable_evaluation and evaluation_deadline to meetings table if not present
    if "enable_evaluation" not in meeting_cols:
        op.add_column(
            "meetings",
            sa.Column(
                "enable_evaluation",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )
    if "evaluation_deadline" not in meeting_cols:
        op.add_column(
            "meetings",
            sa.Column(
                "evaluation_deadline",
                sa.DateTime(),
                nullable=True,
            ),
        )

    # 2. Create meeting_evaluations table if not exists
    existing_tables = insp.get_table_names()
    if "meeting_evaluations" not in existing_tables:
        op.create_table(
            "meeting_evaluations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("meeting_id", sa.Integer(), nullable=False),
            sa.Column("reviewer_id", sa.Integer(), nullable=False),
            sa.Column("target_user_id", sa.Integer(), nullable=False),
            sa.Column("evaluation_type", sa.String(length=50), nullable=False),
            sa.Column(
                "is_anonymous",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column(
                "scores",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
            ),
            sa.Column("average_score", sa.Float(), nullable=False),
            sa.Column("feedback_text", sa.String(length=2000), nullable=True),
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
            sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["target_user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "meeting_id",
                "reviewer_id",
                "target_user_id",
                name="uq_meeting_evaluation",
            ),
        )
        op.create_index(
            op.f("ix_meeting_evaluations_meeting_id"),
            "meeting_evaluations",
            ["meeting_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_meeting_evaluations_reviewer_id"),
            "meeting_evaluations",
            ["reviewer_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_meeting_evaluations_target_user_id"),
            "meeting_evaluations",
            ["target_user_id"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_meeting_evaluations_target_user_id"),
        table_name="meeting_evaluations",
    )
    op.drop_index(
        op.f("ix_meeting_evaluations_reviewer_id"),
        table_name="meeting_evaluations",
    )
    op.drop_index(
        op.f("ix_meeting_evaluations_meeting_id"),
        table_name="meeting_evaluations",
    )
    op.drop_table("meeting_evaluations")
    op.drop_column("meetings", "evaluation_deadline")
    op.drop_column("meetings", "enable_evaluation")
