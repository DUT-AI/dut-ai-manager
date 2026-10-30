"""
Unit tests for UtcDateTime parsing and serialization.
"""

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from pydantic import BaseModel

from app.shared.domain.datetime_types import UtcDateTime, parse_to_utc

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


class SampleDto(BaseModel):
    scheduled_at: UtcDateTime


def test_parse_iso_string_with_z():
    """Chuỗi ISO có Z được parse chính xác về UTC."""
    res = parse_to_utc("2026-10-31T12:30:00Z")
    assert res == datetime(2026, 10, 31, 12, 30, 0, tzinfo=timezone.utc)


def test_parse_iso_string_with_offset():
    """Chuỗi ISO có offset +07:00 được chuyển đổi chính xác về UTC (12:30)."""
    res = parse_to_utc("2026-10-31T19:30:00+07:00")
    assert res == datetime(2026, 10, 31, 12, 30, 0, tzinfo=timezone.utc)


def test_parse_naive_string_defaults_to_vietnam_time():
    """Chuỗi naive không múi giờ (Frontend format) tự động được coi là giờ VN (UTC+7)."""
    res = parse_to_utc("2026-10-31T19:30:00")
    assert res == datetime(2026, 10, 31, 12, 30, 0, tzinfo=timezone.utc)


def test_parse_space_separated_naive_string():
    """Chuỗi naive định dạng YYYY-MM-DD HH:mm:ss."""
    res = parse_to_utc("2026-10-31 19:30:00")
    assert res == datetime(2026, 10, 31, 12, 30, 0, tzinfo=timezone.utc)


def test_parse_naive_datetime_object():
    """Object datetime naive được gán timezone VN rồi đổi sang UTC."""
    naive_dt = datetime(2026, 10, 31, 19, 30, 0)
    res = parse_to_utc(naive_dt)
    assert res == datetime(2026, 10, 31, 12, 30, 0, tzinfo=timezone.utc)


def test_parse_aware_utc_datetime_object():
    """Object datetime đã là UTC aware được giữ nguyên."""
    aware_dt = datetime(2026, 10, 31, 12, 30, 0, tzinfo=timezone.utc)
    res = parse_to_utc(aware_dt)
    assert res == aware_dt


def test_parse_date_object():
    """Object date chuyển thành đầu ngày (00:00:00) theo giờ VN tương ứng 17:00 ngày hôm trước UTC."""
    d = date(2026, 10, 31)
    res = parse_to_utc(d)
    assert res == datetime(2026, 10, 30, 17, 0, 0, tzinfo=timezone.utc)


def test_parse_none_and_empty():
    """Giá trị None hoặc rỗng trả về None."""
    assert parse_to_utc(None) is None
    assert parse_to_utc("") is None
    assert parse_to_utc("   ") is None


def test_parse_invalid_raises_value_error():
    """Định dạng không hợp lệ ném ValueError."""
    with pytest.raises(ValueError):
        parse_to_utc("not-a-valid-date")


def test_pydantic_model_integration():
    """Pydantic model tích hợp UtcDateTime tự động validate và parse input."""
    dto1 = SampleDto(scheduled_at="2026-10-31T19:30:00")
    assert dto1.scheduled_at == datetime(2026, 10, 31, 12, 30, 0, tzinfo=timezone.utc)

    dto2 = SampleDto(scheduled_at="2026-10-31T12:30:00Z")
    assert dto2.scheduled_at == datetime(2026, 10, 31, 12, 30, 0, tzinfo=timezone.utc)


def test_ensure_utc():
    """Hàm ensure_utc bảo đảm datetime luôn là UTC aware."""
    from app.shared.domain.datetime_types import ensure_utc

    # 1. Input đã là UTC aware -> Giữ nguyên
    utc_dt = datetime(2026, 10, 31, 12, 30, 0, tzinfo=timezone.utc)
    assert ensure_utc(utc_dt) == utc_dt

    # 2. Input là naive -> Tự động coi là giờ VN (+7) và convert sang UTC
    naive_dt = datetime(2026, 10, 31, 19, 30, 0)
    assert ensure_utc(naive_dt) == datetime(2026, 10, 31, 12, 30, 0, tzinfo=timezone.utc)

    # 3. Input là timezone khác (ví dụ JST +9) -> Chuyển về đúng UTC
    jst_tz = timezone(timedelta(hours=9))
    jst_dt = datetime(2026, 10, 31, 21, 30, 0, tzinfo=jst_tz)
    assert ensure_utc(jst_dt) == datetime(2026, 10, 31, 12, 30, 0, tzinfo=timezone.utc)
