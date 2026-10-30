"""Safe type parsing and conversion utilities."""

from datetime import datetime


def parse_datetime(val: object) -> datetime | None:
    """Parse datetime an toàn từ str ISO hoặc datetime object."""
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return None
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return None
    return None


def parse_int(val: object) -> int | None:
    """Parse integer an toàn từ int hoặc numeric str."""
    if isinstance(val, int) and not isinstance(val, bool):
        return val
    if isinstance(val, str):
        try:
            return int(val.strip())
        except ValueError:
            return None
    return None
