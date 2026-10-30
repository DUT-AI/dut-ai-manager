"""add_payload_to_permission_requests

Revision ID: 036_permission_payload
Revises: f9a8b7c6d5e4
Create Date: 2026-10-31 02:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "036_permission_payload"
down_revision: str | Sequence[str] | None = "f9a8b7c6d5e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "permission_requests",
        sa.Column(
            "payload",
            sa.JSON(),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("permission_requests", "payload")
