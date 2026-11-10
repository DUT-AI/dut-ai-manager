"""clean_change_meeting

Revision ID: 041_clean_change_meeting
Revises: 040_add_participant_role
Create Date: 2026-11-11 00:26:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "041_clean_change_meeting"
down_revision: str | Sequence[str] | None = "040_add_participant_role"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Xóa các đơn xin đổi ca không hợp lệ (thiếu old_meeting_id hoặc meeting_id) từ phiên bản cũ
    op.execute(
        """
        DELETE FROM permission_requests
        WHERE category = 'CHANGE_MEETING'
          AND (
              payload->>'old_meeting_id' IS NULL
              OR payload->>'meeting_id' IS NULL
              OR payload->>'old_meeting_id' = 'null'
              OR payload->>'meeting_id' = 'null'
          );
        """
    )


def downgrade() -> None:
    # Dữ liệu rác đã xóa không cần khôi phục
    pass
