"""
Unified Datetime Types & Parsers for Enterprise UTC Architecture.

Provides Pydantic types that auto-detect client datetime input:
- Naive strings (e.g. 'YYYY-MM-DDTHH:mm:ss') are interpreted as Vietnam time (Asia/Ho_Chi_Minh)
  and normalized to UTC aware.
- Aware strings (with 'Z' or '+HH:MM' offset) are converted directly to UTC aware.
"""

from datetime import UTC, date, datetime, time
from typing import Annotated, Any
from zoneinfo import ZoneInfo

from pydantic import BeforeValidator, PlainSerializer

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def parse_to_utc(val: Any) -> datetime | None:
    """Normalize any client datetime representation into a timezone-aware UTC datetime."""
    if val is None:
        return None

    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None

        # Standardize 'Z' for fromisoformat compatibility
        clean_val = val.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(clean_val)
        except ValueError:
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y/%m/%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d",
            ):
                try:
                    dt = datetime.strptime(val, fmt)  # noqa: DTZ007
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Invalid datetime format: {val}")

    elif isinstance(val, datetime):
        dt = val
    elif isinstance(val, date):
        # Interpret pure date as start of day in Vietnam timezone
        dt = datetime.combine(val, time.min)
    else:
        raise ValueError(f"Cannot parse value of type {type(val)} to datetime")

    # If datetime is naive (no tzinfo), treat as Vietnam local time (UTC+7)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=VN_TZ)

    # Convert to standard UTC
    return dt.astimezone(UTC)


def serialize_to_iso(val: datetime | None) -> str | None:
    """Serialize UTC datetime to ISO 8601 string."""
    if val is None:
        return None
    return val.isoformat()


# Alias for explicit use in use cases
parse_datetime_to_utc = parse_to_utc
VIETNAM_TZ = VN_TZ


def to_vietnam_time(dt: datetime) -> datetime:
    """Convert UTC aware or naive datetime to Vietnam timezone aware datetime."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=VN_TZ)
    return dt.astimezone(VN_TZ)


def ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime is UTC timezone-aware. Naive is treated as Asia/Ho_Chi_Minh."""
    if dt.tzinfo is not None:
        return dt.astimezone(UTC)
    return dt.replace(tzinfo=VN_TZ).astimezone(UTC)


# Ingestion type for request DTOs
UtcDateTime = Annotated[datetime, BeforeValidator(parse_to_utc)]

# Optional response serializer
IsoDateTime = Annotated[
    datetime | None, PlainSerializer(serialize_to_iso, return_type=str | None)
]
