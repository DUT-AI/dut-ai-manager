"""Unit tests for app.utils.parsers."""

from datetime import UTC, datetime

from app.utils.parsers import parse_datetime, parse_int


def test_parse_datetime_valid_cases():
    now = datetime.now(UTC)
    assert parse_datetime(now) == now

    iso_str = "2026-11-01T08:30:00+00:00"
    dt = parse_datetime(iso_str)
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 11
    assert dt.day == 1
    assert dt.hour == 8
    assert dt.minute == 30

    # Z suffix
    z_str = "2026-11-02T14:00:00Z"
    dt_z = parse_datetime(z_str)
    assert dt_z is not None
    assert dt_z.hour == 14


def test_parse_datetime_invalid_cases():
    assert parse_datetime(None) is None
    assert parse_datetime("") is None
    assert parse_datetime("   ") is None
    assert parse_datetime("not-a-date") is None
    assert parse_datetime(123456) is None
    assert parse_datetime([]) is None


def test_parse_int_valid_cases():
    assert parse_int(42) == 42
    assert parse_int(0) == 0
    assert parse_int(-15) == -15

    # String integer
    assert parse_int("100") == 100
    assert parse_int("  200  ") == 200
    assert parse_int("-50") == -50


def test_parse_int_invalid_cases():
    # Boolean MUST NOT be parsed as int
    assert parse_int(True) is None
    assert parse_int(False) is None

    assert parse_int(None) is None
    assert parse_int("") is None
    assert parse_int("abc") is None
    assert parse_int("12.34") is None
    assert parse_int([1]) is None
    assert parse_int({"val": 1}) is None
