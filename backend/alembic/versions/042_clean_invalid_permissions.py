"""clean_invalid_permissions

Revision ID: 042_clean_invalid_permissions
Revises: 041_clean_change_meeting
Create Date: 2026-11-11 00:35:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "042_clean_invalid_permissions"
down_revision: str | Sequence[str] | None = "041_clean_change_meeting"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Xóa các đơn xin phép không hợp lệ (thiếu dữ liệu bắt buộc trong payload JSON)
    op.execute(
        """
        DELETE FROM permission_requests
        WHERE
            -- Đơn vắng thiếu meeting_id
            (category = 'ABSENCE' AND (
                payload->>'meeting_id' IS NULL
                OR payload->>'meeting_id' = 'null'
            ))
            -- Đơn đi trễ thiếu meeting_id hoặc start_time
            OR (category = 'LATE' AND (
                payload->>'meeting_id' IS NULL
                OR payload->>'meeting_id' = 'null'
                OR payload->>'start_time' IS NULL
                OR payload->>'start_time' = 'null'
            ))
            -- Đơn hoãn bài tập thiếu homework_id hoặc start_time
            OR (category = 'POSTPONE' AND (
                payload->>'homework_id' IS NULL
                OR payload->>'homework_id' = 'null'
                OR payload->>'start_time' IS NULL
                OR payload->>'start_time' = 'null'
            ))
            -- Đơn đổi ca thiếu meeting_id hoặc old_meeting_id
            OR (category = 'CHANGE_MEETING' AND (
                payload->>'meeting_id' IS NULL
                OR payload->>'meeting_id' = 'null'
                OR payload->>'old_meeting_id' IS NULL
                OR payload->>'old_meeting_id' = 'null'
            ));
        """
    )


def downgrade() -> None:
    # Dữ liệu rác đã xóa không cần khôi phục
    pass
