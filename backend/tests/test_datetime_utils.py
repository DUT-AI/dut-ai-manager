from datetime import UTC, datetime, timezone, timedelta
from app.utils.datetime import to_utc7_naive, get_current_utc7_time


def test_to_utc7_naive_none():
    assert to_utc7_naive(None) is None


def test_to_utc7_naive_empty_or_invalid_string():
    assert to_utc7_naive("") is None
    assert to_utc7_naive("   ") is None
    assert to_utc7_naive("invalid-date-string") is None


def test_to_utc7_naive_with_iso_z_string():
    # 2026-10-06 10:00:00 UTC -> 2026-10-06 17:00:00 ICT
    res = to_utc7_naive("2026-10-06T10:00:00Z")
    assert res is not None
    assert res.tzinfo is None
    assert res == datetime(2026, 10, 6, 17, 0, 0)


def test_to_utc7_naive_with_iso_offset_string():
    # 2026-10-06 10:00:00+00:00 -> 2026-10-06 17:00:00 ICT
    res = to_utc7_naive("2026-10-06T10:00:00+00:00")
    assert res is not None
    assert res.tzinfo is None
    assert res == datetime(2026, 10, 6, 17, 0, 0)

    # 2026-10-06 17:00:00+07:00 -> 2026-10-06 17:00:00 ICT
    res7 = to_utc7_naive("2026-10-06T17:00:00+07:00")
    assert res7 is not None
    assert res7.tzinfo is None
    assert res7 == datetime(2026, 10, 6, 17, 0, 0)


def test_to_utc7_naive_with_naive_string():
    res = to_utc7_naive("2026-10-06 18:30:00")
    assert res is not None
    assert res.tzinfo is None
    assert res == datetime(2026, 10, 6, 18, 30, 0)


def test_to_utc7_naive_with_aware_datetime():
    utc_dt = datetime(2026, 10, 6, 10, 0, 0, tzinfo=UTC)
    res = to_utc7_naive(utc_dt)
    assert res is not None
    assert res.tzinfo is None
    assert res == datetime(2026, 10, 6, 17, 0, 0)


def test_to_utc7_naive_with_naive_datetime():
    naive_dt = datetime(2026, 10, 6, 18, 30, 0)
    res = to_utc7_naive(naive_dt)
    assert res is not None
    assert res.tzinfo is None
    assert res == naive_dt
