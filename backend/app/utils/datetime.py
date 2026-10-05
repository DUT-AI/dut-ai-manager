from datetime import UTC, datetime, timedelta, timezone

ICT_TZ = timezone(timedelta(hours=7))


def get_current_utc7_time() -> datetime:
    """Trả về naive datetime mang giá trị giờ hiện tại của Việt Nam (ICT, UTC+7)."""
    return (datetime.now(UTC) + timedelta(hours=7)).replace(tzinfo=None)


def to_utc7_naive(dt: datetime | None) -> datetime | None:
    """
    Chuẩn hóa datetime về naive datetime giờ Việt Nam (UTC+7):
    - Nếu dt có tzinfo (aware): chuyển sang múi giờ ICT rồi bỏ tzinfo.
    - Nếu dt là naive: giữ nguyên.
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(ICT_TZ).replace(tzinfo=None)
    return dt
