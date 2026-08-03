"""update_homework_status_enum

Revision ID: 34d5f201eeab
Revises: bc466a293297
Create Date: 2026-01-09 17:31:17.160870

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "34d5f201eeab"
down_revision: str | Sequence[str] | None = "bc466a293297"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - Update HomeworkStatus enum."""
    # Add new enum value - must be outside transaction for PostgreSQL
    op.execute("COMMIT")
    op.execute("ALTER TYPE homeworkstatus ADD VALUE IF NOT EXISTS 'leader đã check'")


def downgrade() -> None:
    """Downgrade schema."""
    # PostgreSQL doesn't support removing enum values directly
    pass
