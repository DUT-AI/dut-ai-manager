"""Enterprise Datetime Utilities.

Re-exports and timezone constants for consistent UTC and Vietnam (UTC+7)
datetime handling.
Legacy naive helper `get_current_utc7_time()` has been permanently removed in favor of:
`datetime.now(timezone.utc)` for current timestamps.
"""

from datetime import timedelta, timezone

from app.shared.domain.datetime_types import (
    VIETNAM_TZ,
    IsoDateTime,
    UtcDateTime,
    ensure_utc,
    parse_datetime_to_utc,
    parse_to_utc,
    to_vietnam_time,
)

ICT_TZ = timezone(timedelta(hours=7))

__all__ = [
    "ICT_TZ",
    "VIETNAM_TZ",
    "IsoDateTime",
    "UtcDateTime",
    "ensure_utc",
    "parse_datetime_to_utc",
    "parse_to_utc",
    "to_vietnam_time",
]
