"""fix_participant_timestamptz

Convert remaining naive timestamp columns (meeting_participants.check_in_at,
check_out_at, meetings.evaluation_deadline, etc.) to TIMESTAMPTZ (UTC).

Revision ID: 038_fix_participant_timestamptz
Revises: 037_drop_perm_legacy_cols
Create Date: 2026-10-31 04:05:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "038_fix_participant_timestamptz"
down_revision: str | Sequence[str] | None = "037_drop_perm_legacy_cols"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TARGET_COLUMNS = [
    ("meeting_participants", "check_in_at"),
    ("meeting_participants", "check_out_at"),
    ("meetings", "evaluation_deadline"),
    ("homework_assignees", "created_at"),
    ("homework_assignees", "updated_at"),
    ("monthly_user_stats", "created_at"),
    ("monthly_user_stats", "updated_at"),
]


def upgrade() -> None:
    """Convert naive timestamp columns to timestamp with time zone (UTC)."""
    for table, col in TARGET_COLUMNS:
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                      AND table_name = '{table}' 
                      AND column_name = '{col}'
                      AND data_type = 'timestamp without time zone'
                ) THEN
                    ALTER TABLE {table} 
                    ALTER COLUMN {col} TYPE timestamp with time zone 
                    USING {col} AT TIME ZONE 'UTC';
                END IF;
            END $$;
            """
        )


def downgrade() -> None:
    """Convert columns back to timestamp without time zone if rolled back."""
    for table, col in TARGET_COLUMNS:
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                      AND table_name = '{table}' 
                      AND column_name = '{col}'
                      AND data_type = 'timestamp with time zone'
                ) THEN
                    ALTER TABLE {table} 
                    ALTER COLUMN {col} TYPE timestamp without time zone 
                    USING {col} AT TIME ZONE 'UTC';
                END IF;
            END $$;
            """
        )
