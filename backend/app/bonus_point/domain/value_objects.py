from enum import StrEnum


class BonusPointType(StrEnum):
    """Phân loại điểm cộng trong hệ thống (2 loại: CLUB_ACTIVITY và OTHER)."""

    CLUB_ACTIVITY = "CLUB_ACTIVITY"  # Điểm hoạt động tại CLB / Lab
    OTHER = "OTHER"  # Điểm cộng khác (sinh hoạt, khen thưởng,...)


def infer_bonus_point_type(reason: str | None) -> BonusPointType:
    """Tự động suy luận loại điểm cộng từ chuỗi lý do (reason)."""
    if not reason:
        return BonusPointType.OTHER
    r = reason.strip().lower()
    if "hoạt động tại clb" in r or "clb" in r or "lab" in r or "rèn luyện" in r:
        return BonusPointType.CLUB_ACTIVITY
    return BonusPointType.OTHER
