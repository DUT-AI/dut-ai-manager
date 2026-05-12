from datetime import datetime
from typing import ClassVar, Optional
from pydantic import BaseModel
from enum import Enum


class ParticipantStatus(str, Enum):
    """Trạng thái tham dự buổi họp"""

    NOT_JOINED = "chưa tham gia"
    JOINED = "đã checkin"
    COMPLETED = "đã checkout"


class CapacityStatus(str, Enum):
    SAFE = "safe"  # < 15 người
    WARNING = "warning"  # 15-19 người
    OVERLOAD = "overload"  # >= 20 người


class CapacityMonitor(BaseModel):
    """Trạng thái cảnh báo quá tải (Value Object)"""

    MAX_CAPACITY: ClassVar[int] = 20
    WARNING_THRESHOLD: ClassVar[int] = 15
    OVERLOAD_THRESHOLD: ClassVar[int] = 20
    FORECAST_WINDOW_MINUTES: ClassVar[int] = 30
    EPSILON: ClassVar[int] = 2

    current_count: int = 0
    incoming_count: int = 0
    outgoing_count: int = 0
    future_count: int = 0
    epsilon: int = 2  # Use literal or field default

    status: CapacityStatus = CapacityStatus.SAFE
    last_updated: datetime

    @classmethod
    def calculate(
        cls,
        n_current: int,
        n_incoming: int,
        n_outgoing: int,
        epsilon: int = 2,
    ) -> "CapacityMonitor":
        """Tính toán capacity từ các thành phần"""
        n_future = n_current + n_incoming - n_outgoing + epsilon

        if n_future >= cls.OVERLOAD_THRESHOLD:
            status = CapacityStatus.OVERLOAD
        elif n_future >= cls.WARNING_THRESHOLD:
            status = CapacityStatus.WARNING
        else:
            status = CapacityStatus.SAFE

        return cls(
            current_count=n_current,
            incoming_count=n_incoming,
            outgoing_count=n_outgoing,
            future_count=n_future,
            epsilon=epsilon,
            status=status,
            last_updated=datetime.utcnow(),
        )
