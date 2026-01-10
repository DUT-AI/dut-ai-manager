"""fix_leader_checked_enum

Revision ID: 4291020226ce
Revises: 053e3c2e8527
Create Date: 2026-01-09 21:01:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "4291020226ce"
down_revision: Union[str, Sequence[str], None] = "053e3c2e8527"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add LEADER_CHECKED to enum if it doesn't exist."""
    # First commit any transaction to allow ALTER TYPE
    op.execute("COMMIT")
    # Add new enum value (PostgreSQL requires this to be outside transaction)
    op.execute("ALTER TYPE homeworkstatus ADD VALUE IF NOT EXISTS 'LEADER_CHECKED'")


def downgrade() -> None:
    """Cannot remove enum values in PostgreSQL."""
    pass
