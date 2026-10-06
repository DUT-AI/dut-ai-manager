"""backfill_exercise_id_for_coding_submissions

Revision ID: e8d7c6b5a4f3
Revises: d3a2b1c4e5f6
Create Date: 2026-10-06 14:55:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e8d7c6b5a4f3"
down_revision: str | Sequence[str] | None = "d3a2b1c4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Backfill exercise_id cho các bài nộp CODING cũ trong database
    # Sử dụng submission_id trong details nếu có, hoặc sinh key 'legacy-<homework_id>-<id>'
    op.execute(
        """
        UPDATE homework_submissions
        SET exercise_id = COALESCE(
            NULLIF(details->>'submission_id', ''),
            'legacy-' || homework_id::text || '-' || id::text
        )
        WHERE (UPPER(submission_type) = 'CODING' OR submission_type IS NULL)
          AND (exercise_id IS NULL OR exercise_id = '');
        """
    )


def downgrade() -> None:
    pass
