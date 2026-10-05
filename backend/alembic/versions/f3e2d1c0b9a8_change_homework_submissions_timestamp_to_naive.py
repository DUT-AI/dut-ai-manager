"""change_homework_submissions_timestamp_to_naive

Revision ID: f3e2d1c0b9a8
Revises: 235acc57f519
Create Date: 2026-10-05 15:30:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f3e2d1c0b9a8"
down_revision: str | Sequence[str] | None = "235acc57f519"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to use naive timestamp without timezone, matching system convention."""
    op.execute(
        "ALTER TABLE homework_submissions ALTER COLUMN submitted_at TYPE timestamp without time zone USING submitted_at AT TIME ZONE 'UTC';"
    )
    op.execute(
        "ALTER TABLE homework_submissions ALTER COLUMN created_at TYPE timestamp without time zone USING created_at AT TIME ZONE 'UTC';"
    )
    op.execute(
        "UPDATE homework_submissions SET created_at = submitted_at WHERE created_at < submitted_at - interval '6 hours';"
    )


def downgrade() -> None:
    """Downgrade schema back to timestamp with timezone."""
    op.execute(
        "ALTER TABLE homework_submissions ALTER COLUMN submitted_at TYPE timestamp with time zone USING submitted_at AT TIME ZONE 'UTC';"
    )
    op.execute(
        "ALTER TABLE homework_submissions ALTER COLUMN created_at TYPE timestamp with time zone USING created_at AT TIME ZONE 'UTC';"
    )
