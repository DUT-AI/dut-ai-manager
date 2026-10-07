"""add_old_meeting_id_to_permission_requests

Revision ID: a8f1b2c3d4e5
Revises: f5a6b7c8d9e0
Create Date: 2026-10-07 22:15:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a8f1b2c3d4e5"
down_revision: str | Sequence[str] | None = "f5a6b7c8d9e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns("permission_requests")]

    if "old_meeting_id" not in cols:
        op.add_column(
            "permission_requests",
            sa.Column(
                "old_meeting_id",
                sa.Integer(),
                sa.ForeignKey("meetings.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
        op.create_index(
            "ix_permission_requests_old_meeting_id",
            "permission_requests",
            ["old_meeting_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns("permission_requests")]

    if "old_meeting_id" in cols:
        op.drop_index(
            "ix_permission_requests_old_meeting_id",
            table_name="permission_requests",
        )
        op.drop_column("permission_requests", "old_meeting_id")
