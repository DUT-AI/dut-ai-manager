"""convert_timestamps_to_timestamptz

Revision ID: f9a8b7c6d5e4
Revises: 9a1b2c3d4e5f
Create Date: 2026-10-30 17:15:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f9a8b7c6d5e4"
down_revision: str | Sequence[str] | None = "9a1b2c3d4e5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Danh sách các bảng và cột cần chuyển sang TIMESTAMPTZ
TARGET_COLUMNS = [
    ("meetings", "start_time"),
    ("meetings", "end_time"),
    ("meetings", "created_at"),
    ("meetings", "updated_at"),
    ("meeting_participants", "check_in_time"),
    ("meeting_participants", "check_out_time"),
    ("meeting_participants", "created_at"),
    ("meeting_participants", "updated_at"),
    ("meeting_evaluations", "created_at"),
    ("meeting_evaluations", "updated_at"),
    ("meeting_overall_evaluations", "created_at"),
    ("meeting_overall_evaluations", "updated_at"),
    ("homeworks", "deadline"),
    ("homeworks", "created_at"),
    ("homeworks", "updated_at"),
    ("homework_submissions", "submitted_at"),
    ("homework_submissions", "created_at"),
    ("homework_submissions", "updated_at"),
    ("cleaning_duties", "submitted_at"),
    ("cleaning_duties", "approved_at"),
    ("cleaning_duties", "rejected_at"),
    ("cleaning_duties", "created_at"),
    ("cleaning_duties", "updated_at"),
    ("permission_requests", "start_time"),
    ("permission_requests", "end_time"),
    ("permission_requests", "created_at"),
    ("permission_requests", "updated_at"),
    ("violations", "created_at"),
    ("violations", "updated_at"),
    ("bonus_points", "created_at"),
    ("bonus_points", "updated_at"),
    ("notifications", "read_at"),
    ("notifications", "created_at"),
    ("notifications", "updated_at"),
    ("accounts", "created_at"),
    ("accounts", "updated_at"),
    ("users", "created_at"),
    ("users", "updated_at"),
    ("roles", "created_at"),
    ("roles", "updated_at"),
    ("permissions", "created_at"),
    ("permissions", "updated_at"),
    ("user_roles", "created_at"),
    ("user_roles", "updated_at"),
    ("role_permissions", "created_at"),
    ("role_permissions", "updated_at"),
    ("role_api_keys", "created_at"),
    ("role_api_keys", "updated_at"),
    ("invoices", "created_at"),
    ("invoices", "updated_at"),
    ("outgoing_invoices", "created_at"),
    ("outgoing_invoices", "updated_at"),
    ("invoice_items", "created_at"),
    ("invoice_items", "updated_at"),
    ("teams", "created_at"),
    ("teams", "updated_at"),
    ("team_members", "created_at"),
    ("team_members", "updated_at"),
    ("push_subscriptions", "created_at"),
    ("push_subscriptions", "updated_at"),
    ("push_subscriptions", "last_used_at"),
]


def upgrade() -> None:
    """Chuyển đổi toàn bộ cột naive timestamp sang timestamptz có timezone (UTC), quy chiếu từ giờ Việt Nam."""
    for table, col in TARGET_COLUMNS:
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = '{col}'
                ) THEN
                    ALTER TABLE {table} 
                    ALTER COLUMN {col} TYPE timestamp with time zone 
                    USING {col} AT TIME ZONE 'Asia/Ho_Chi_Minh';
                END IF;
            END $$;
            """
        )


def downgrade() -> None:
    """Chuyển đổi ngược lại về naive timestamp nếu cần rollback."""
    for table, col in TARGET_COLUMNS:
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = '{col}'
                ) THEN
                    ALTER TABLE {table} 
                    ALTER COLUMN {col} TYPE timestamp without time zone 
                    USING {col} AT TIME ZONE 'Asia/Ho_Chi_Minh';
                END IF;
            END $$;
            """
        )
