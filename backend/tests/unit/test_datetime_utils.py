"""Tests for datetime utilities in app.utils.datetime."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.utils.datetime import (
    ICT_TZ,
    VIETNAM_TZ,
    parse_datetime_to_utc,
    to_vietnam_time,
)


def test_vietnam_timezone_constant():
    assert VIETNAM_TZ == ZoneInfo("Asia/Ho_Chi_Minh")
    assert ICT_TZ is not None


def test_parse_datetime_to_utc():
    # Naive assumed Asia/Ho_Chi_Minh (+07:00)
    naive = datetime(2026, 10, 31, 14, 0, 0)
    utc_dt = parse_datetime_to_utc(naive)
    assert utc_dt.tzinfo == timezone.utc
    assert utc_dt == datetime(2026, 10, 31, 7, 0, 0, tzinfo=timezone.utc)


def test_to_vietnam_time():
    utc_dt = datetime(2026, 10, 31, 7, 0, 0, tzinfo=timezone.utc)
    vn_dt = to_vietnam_time(utc_dt)
    assert vn_dt.hour == 14
    assert vn_dt.day == 31
