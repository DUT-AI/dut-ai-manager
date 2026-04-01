from enum import Enum


class RequestCategory(str, Enum):
    """Phân loại yêu cầu xin phép (Domain Value Object)"""

    ABSENCE = "ABSENCE"  # Xin vắng sinh hoạt
    POSTPONE = "POSTPONE"  # Xin hoãn bài tập
    OTHER = "OTHER"  # Khác
