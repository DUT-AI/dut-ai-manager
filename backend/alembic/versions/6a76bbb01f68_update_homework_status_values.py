"""update_homework_status_values

Revision ID: 6a76bbb01f68
Revises: 6706609c25d4
Create Date: 2026-01-09 21:09:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6a76bbb01f68"
down_revision: Union[str, Sequence[str], None] = "6706609c25d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update existing data to use Enum values instead of names."""
    # Commit transaction to ensure data integrity
    op.execute("COMMIT")

    # Update 'NOT_SUBMITTED' -> 'chưa nộp'
    op.execute(
        "UPDATE homework_submissions SET status = 'chưa nộp' WHERE status = 'NOT_SUBMITTED'"
    )

    # Update 'SUBMITTED' -> 'đã nộp'
    op.execute(
        "UPDATE homework_submissions SET status = 'đã nộp' WHERE status = 'SUBMITTED'"
    )

    # Update 'PENDING_LEADER_REVIEW' -> 'leader đã check' - assuming this maps here or 'chờ leader check'?
    # Based on previous context, user wanted 'LeaderChecked' -> 'leader đã check'
    # Let's cover possible old keys just in case
    op.execute(
        "UPDATE homework_submissions SET status = 'leader đã check' WHERE status IN ('PENDING_LEADER_REVIEW', 'LEADER_CHECKED', 'LeaderChecked')"
    )

    # Update 'PENDING_ADMIN_REVIEW' -> 'leader đã check' (seems unused but safe to map)
    op.execute(
        "UPDATE homework_submissions SET status = 'leader đã check' WHERE status = 'PENDING_ADMIN_REVIEW'"
    )

    # Update 'FINISHED' -> 'finish'
    op.execute(
        "UPDATE homework_submissions SET status = 'finish' WHERE status = 'FINISHED'"
    )


def downgrade() -> None:
    """Revert data changes (optional, complicated mapping back)."""
    pass
