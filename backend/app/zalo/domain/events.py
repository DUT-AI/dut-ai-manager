from dataclasses import dataclass

from app.shared.domain import DomainEvent


@dataclass
class ZaloAccountBound(DomainEvent):
    """Sự kiện tài khoản Zalo được liên kết qua OAuth"""

    user_id: int
    zalo_id: str
    zalo_name: str


@dataclass
class ZaloBotLinked(DomainEvent):
    """Sự kiện tài khoản Zalo được liên kết qua Zalo Bot (Bind Code)"""

    user_id: int
    zalo_bot_id: str
    user_name: str
