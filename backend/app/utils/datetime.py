from datetime import UTC, datetime, timedelta


def get_current_utc7_time():
    return (datetime.now(UTC) + timedelta(hours=7)).replace(tzinfo=None)
