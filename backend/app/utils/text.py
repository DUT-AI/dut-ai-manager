"""Tiện ích xử lý chuỗi."""

import unicodedata


def remove_vietnamese_tones(s: str) -> str:
    """Bỏ dấu tiếng Việt (đ/Đ xử lý riêng, còn lại qua NFD + bỏ ký tự kết hợp)."""
    if not s:
        return s
    s = s.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", s)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")
