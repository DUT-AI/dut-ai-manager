from datetime import datetime, timedelta, timezone


def get_current_utc7_time():
    return (datetime.now(timezone.utc) + timedelta(hours=7)).replace(tzinfo=None)
