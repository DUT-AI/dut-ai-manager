from datetime import datetime, timedelta


def get_current_utc7_time():
    return datetime.utcnow() + timedelta(hours=7)
