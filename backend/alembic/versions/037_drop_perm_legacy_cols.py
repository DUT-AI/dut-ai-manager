"""sync_payload_and_drop_legacy_columns

Revision ID: 037_drop_perm_legacy_cols
Revises: 036_permission_payload
Create Date: 2026-10-31 03:15:00.000000

"""

import json
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "037_drop_perm_legacy_cols"
down_revision: str | Sequence[str] | None = "036_permission_payload"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _build_row_payload(row: Any) -> dict[str, object] | None:
    current_payload = row.payload
    if (
        isinstance(current_payload, dict)
        and current_payload
        and "category" in current_payload
    ):
        return None

    category = row.category
    meeting_id = row.meeting_id
    old_meeting_id = row.old_meeting_id
    homework_id = row.homework_id
    start_time = row.start_time

    payload_dict: dict[str, object] = {"category": category}

    match category:
        case "ABSENCE":
            payload_dict["meeting_id"] = meeting_id
        case "LATE":
            payload_dict["meeting_id"] = meeting_id
            payload_dict["start_time"] = (
                start_time.isoformat() if start_time else None
            )
        case "POSTPONE":
            payload_dict["homework_id"] = homework_id
            payload_dict["start_time"] = (
                start_time.isoformat() if start_time else None
            )
        case "CHANGE_MEETING":
            payload_dict["meeting_id"] = meeting_id
            payload_dict["old_meeting_id"] = old_meeting_id
            payload_dict["start_time"] = (
                start_time.isoformat() if start_time else None
            )
        case "OTHER":
            pass
        case _:
            if meeting_id is not None:
                payload_dict["meeting_id"] = meeting_id
            if homework_id is not None:
                payload_dict["homework_id"] = homework_id
            if start_time is not None:
                payload_dict["start_time"] = start_time.isoformat()

    return payload_dict


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Đồng bộ dữ liệu hiện có từ các cột cũ sang cột payload
    stmt = sa.text(
        "SELECT id, category, meeting_id, old_meeting_id, homework_id, "
        "start_time, payload FROM permission_requests"
    )
    rows = bind.execute(stmt).fetchall()

    for row in rows:
        payload_dict = _build_row_payload(row)
        if payload_dict is not None:
            bind.execute(
                sa.text(
                    "UPDATE permission_requests SET payload = :payload "
                    "WHERE id = :id"
                ),
                {"payload": json.dumps(payload_dict), "id": row.id},
            )

    # 2. Xóa các Index trên các cột cũ nếu tồn tại
    op.drop_index(
        "ix_permission_requests_homework_id",
        table_name="permission_requests",
        if_exists=True,
    )
    op.drop_index(
        "ix_permission_requests_meeting_id",
        table_name="permission_requests",
        if_exists=True,
    )
    op.drop_index(
        "ix_permission_requests_old_meeting_id",
        table_name="permission_requests",
        if_exists=True,
    )

    # 3. Xóa các Foreign Key Constraints trên các cột cũ
    op.drop_constraint(
        "permission_requests_homework_id_fkey",
        "permission_requests",
        type_="foreignkey",
    )
    op.drop_constraint(
        "permission_requests_meeting_id_fkey",
        "permission_requests",
        type_="foreignkey",
    )
    op.drop_constraint(
        "permission_requests_old_meeting_id_fkey",
        "permission_requests",
        type_="foreignkey",
    )

    # 4. Xóa các cột cũ
    op.drop_column("permission_requests", "homework_id")
    op.drop_column("permission_requests", "meeting_id")
    op.drop_column("permission_requests", "old_meeting_id")
    op.drop_column("permission_requests", "start_time")

    # 5. Tạo JSON expression indexes để tăng tốc các truy vấn theo ID
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_permission_requests_payload_meeting_id "
        "ON permission_requests (((payload->>'meeting_id')::integer))"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_permission_requests_payload_homework_id "
        "ON permission_requests (((payload->>'homework_id')::integer))"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS "
        "ix_permission_requests_payload_old_meeting_id "
        "ON permission_requests (((payload->>'old_meeting_id')::integer))"
    )


def downgrade() -> None:
    # 1. Xóa các JSON expression indexes
    op.execute("DROP INDEX IF EXISTS ix_permission_requests_payload_meeting_id")
    op.execute("DROP INDEX IF EXISTS ix_permission_requests_payload_homework_id")
    op.execute(
        "DROP INDEX IF EXISTS ix_permission_requests_payload_old_meeting_id"
    )

    # 2. Thêm lại các cột cũ
    op.add_column(
        "permission_requests",
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "permission_requests",
        sa.Column("homework_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "permission_requests",
        sa.Column("meeting_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "permission_requests",
        sa.Column("old_meeting_id", sa.Integer(), nullable=True),
    )

    # 3. Phục hồi dữ liệu từ payload ngược về các cột
    op.execute(
        "UPDATE permission_requests "
        "SET meeting_id = (payload->>'meeting_id')::integer "
        "WHERE payload->>'meeting_id' IS NOT NULL"
    )
    op.execute(
        "UPDATE permission_requests "
        "SET homework_id = (payload->>'homework_id')::integer "
        "WHERE payload->>'homework_id' IS NOT NULL"
    )
    op.execute(
        "UPDATE permission_requests "
        "SET old_meeting_id = (payload->>'old_meeting_id')::integer "
        "WHERE payload->>'old_meeting_id' IS NOT NULL"
    )
    op.execute(
        "UPDATE permission_requests "
        "SET start_time = (payload->>'start_time')::timestamptz "
        "WHERE payload->>'start_time' IS NOT NULL"
    )

    # 4. Thêm lại constraints và indexes
    op.create_foreign_key(
        "permission_requests_homework_id_fkey",
        "permission_requests",
        "homeworks",
        ["homework_id"],
        ["id"],
    )
    op.create_foreign_key(
        "permission_requests_meeting_id_fkey",
        "permission_requests",
        "meetings",
        ["meeting_id"],
        ["id"],
    )
    op.create_foreign_key(
        "permission_requests_old_meeting_id_fkey",
        "permission_requests",
        "meetings",
        ["old_meeting_id"],
        ["id"],
    )
    op.create_index(
        "ix_permission_requests_homework_id",
        "permission_requests",
        ["homework_id"],
    )
    op.create_index(
        "ix_permission_requests_meeting_id",
        "permission_requests",
        ["meeting_id"],
    )
    op.create_index(
        "ix_permission_requests_old_meeting_id",
        "permission_requests",
        ["old_meeting_id"],
    )
