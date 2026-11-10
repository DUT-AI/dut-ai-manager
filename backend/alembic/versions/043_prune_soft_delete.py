"""prune_soft_delete

Revision ID: 043_prune_soft_delete
Revises: 042_clean_invalid_permissions
Create Date: 2026-11-11 01:34:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "043_prune_soft_delete"
down_revision: str | Sequence[str] | None = "042_clean_invalid_permissions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PRUNE_TABLES = [
    "meeting_participants",
    "meeting_evaluations",
    "meeting_overall_evaluations",
    "meetings",
    "homework_assignees",
    "homeworks",
    "team_members",
    "teams",
    "user_roles",
    "notifications",
    "push_subscriptions",
    "permissions",
    "roles",
    "monthly_user_stats",
    "invoice_items",
    "cleaning_duties",
]


def upgrade() -> None:
    # 1. Dọn dẹp an toàn các bản ghi con trước khi xóa bản ghi cha
    op.execute(
        """
        -- Xóa đánh giá và người tham dự của các buổi học đã xóa mềm
        DELETE FROM meeting_evaluations WHERE meeting_id IN (SELECT id FROM meetings WHERE is_deleted = true);
        DELETE FROM meeting_overall_evaluations WHERE meeting_id IN (SELECT id FROM meetings WHERE is_deleted = true);
        DELETE FROM meeting_participants WHERE meeting_id IN (SELECT id FROM meetings WHERE is_deleted = true);
        DELETE FROM meeting_participants WHERE is_deleted = true;
        DELETE FROM meetings WHERE is_deleted = true;

        -- Xóa phân công và bài nộp của các bài tập đã xóa mềm
        DELETE FROM homework_assignees WHERE homework_id IN (SELECT id FROM homeworks WHERE is_deleted = true);
        DELETE FROM homework_submissions WHERE homework_id IN (SELECT id FROM homeworks WHERE is_deleted = true);
        DELETE FROM homeworks WHERE is_deleted = true;

        -- Xóa thành viên nhóm đã xóa mềm
        DELETE FROM team_members WHERE is_deleted = true;
        """
    )

    # 2. Xóa 2 cột rác không có dữ liệu trên bảng homeworks
    op.execute(
        """
        ALTER TABLE homeworks DROP COLUMN IF EXISTS homework_slug;
        ALTER TABLE homeworks DROP COLUMN IF EXISTS game_slug;
        """
    )

    # 3. Drop cột is_deleted trên các bảng chuyển sang Hard Delete
    for table in PRUNE_TABLES:
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS is_deleted;")


def downgrade() -> None:
    # Khôi phục cột is_deleted nếu cần rollback
    for table in PRUNE_TABLES:
        op.add_column(
            table,
            sa.Column(
                "is_deleted",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )
