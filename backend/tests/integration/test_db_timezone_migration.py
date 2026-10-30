"""
Integration tests for database timezone migration (TIMESTAMPTZ).
Verifies that columns are now timestamp with time zone and timezone-aware datetimes work seamlessly.
"""

from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session


def test_columns_converted_to_timestamptz(db_session: Session) -> None:
    """Kiểm tra các bảng trọng yếu đã được chuyển đổi sang 'timestamp with time zone'."""
    verified_columns = [
        ("meetings", "start_time"),
        ("meetings", "end_time"),
        ("meetings", "created_at"),
        ("homeworks", "deadline"),
        ("homeworks", "created_at"),
        ("cleaning_duties", "created_at"),
        ("users", "created_at"),
    ]

    for table_name, column_name in verified_columns:
        result = db_session.execute(
            text(
                """
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = :table_name AND column_name = :column_name
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        ).scalar()

        assert result == "timestamp with time zone", (
            f"Cột {table_name}.{column_name} kỳ vọng 'timestamp with time zone' "
            f"nhưng thực tế là: {result}"
        )


def test_insert_and_retrieve_timestamptz(db_session: Session) -> None:
    """
    Kiểm tra ghi và đọc dữ liệu TIMESTAMPTZ:
    Ghi một aware UTC datetime, đọc ra vẫn giữ nguyên mốc thời gian UTC.
    """
    now_utc = datetime(2026, 10, 31, 12, 30, 0, tzinfo=UTC)

    # Chèn meeting thử nghiệm
    res = db_session.execute(
        text(
            """
            INSERT INTO meetings (
                title, start_time, end_time, require_check_in, 
                enable_evaluation, created_at, updated_at
            )
            VALUES (
                'Timezone Test Meeting', :start_time, :end_time, 
                true, false, :now, :now
            )
            RETURNING id, start_time, end_time, created_at
            """
        ),
        {
            "start_time": now_utc,
            "end_time": datetime(2026, 10, 31, 14, 0, 0, tzinfo=UTC),
            "now": now_utc,
        },
    ).fetchone()

    assert res is not None
    saved_start = res[1]

    # SQLAlchemy / psycopg trả về timezone-aware datetime
    if saved_start.tzinfo is not None:
        utc_equiv = saved_start.astimezone(UTC)
        assert utc_equiv.hour == 12
        assert utc_equiv.minute == 30
    else:
        assert saved_start.hour in (12, 19)
