from datetime import UTC, datetime, timedelta, timezone

ICT_TZ = timezone(timedelta(hours=7))


def get_current_utc7_time() -> datetime:
    """Trả về naive datetime mang giá trị giờ hiện tại của Việt Nam (ICT, UTC+7)."""
    return (datetime.now(UTC) + timedelta(hours=7)).replace(tzinfo=None)


def to_utc7_naive(dt: datetime | str | None) -> datetime | None:
    """
    Chuẩn hóa datetime hoặc chuỗi ISO/timestamp về naive datetime giờ Việt Nam (UTC+7):
    - Nếu dt là str: parse thành datetime. Nếu có timezone thì chuyển sang múi giờ ICT rồi bỏ tzinfo.
    - Nếu dt có tzinfo (aware): chuyển sang múi giờ ICT rồi bỏ tzinfo.
    - Nếu dt là naive: giữ nguyên.
    """
    if dt is None:
        return None

    if isinstance(dt, str):
        val = dt.strip()
        if not val:
            return None
        try:
            # Hỗ trợ ISO 8601 (bao gồm Z, offset +HH:MM, space, ...)
            dt_obj = datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y/%m/%d %H:%M:%S",
                "%Y-%m-%d",
            ):
                try:
                    dt_obj = datetime.strptime(val, fmt)
                    break
                except ValueError:
                    continue
            else:
                return None

        if dt_obj.tzinfo is not None:
            return dt_obj.astimezone(ICT_TZ).replace(tzinfo=None)
        return dt_obj

    if isinstance(dt, datetime):
        if dt.tzinfo is not None:
            return dt.astimezone(ICT_TZ).replace(tzinfo=None)
        return dt

    return None

