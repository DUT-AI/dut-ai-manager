from datetime import UTC, datetime
from enum import Enum
from typing import ClassVar

from pydantic import BaseModel


class ParticipantStatus(str, Enum):
    """Trạng thái tham dự buổi họp"""

    NOT_JOINED = "NOT_JOINED"
    JOINED = "JOINED"
    COMPLETED = "COMPLETED"


class CapacityStatus(str, Enum):
    SAFE = "SAFE"  # < 2 người
    WARNING = "WARNING"  # = 2 người
    OVERLOAD = "OVERLOAD"  # >= 3 người


class CapacityMonitor(BaseModel):
    """Trạng thái cảnh báo quá tải (Value Object)"""

    MAX_CAPACITY: ClassVar[int] = 3
    WARNING_THRESHOLD: ClassVar[int] = 2
    OVERLOAD_THRESHOLD: ClassVar[int] = 3
    FORECAST_WINDOW_MINUTES: ClassVar[int] = 30
    EPSILON: ClassVar[int] = 0

    current_count: int = 0
    incoming_count: int = 0
    outgoing_count: int = 0
    future_count: int = 0
    epsilon: int = 0  # Use literal or field default
    max_capacity: int = 3

    status: CapacityStatus = CapacityStatus.SAFE
    last_updated: datetime

    @classmethod
    def calculate(
        cls,
        n_current: int,
        n_incoming: int,
        n_outgoing: int,
        epsilon: int = 0,
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
            max_capacity=cls.MAX_CAPACITY,
            status=status,
            last_updated=datetime.now(UTC),
        )
