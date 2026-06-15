"""
Violation Domain Entity — pure Pydantic, NO ORM dependency.

Contains business rules and validation for violations.
"""

from datetime import datetime
from enum import Enum

from pydantic import field_validator

from app.shared.domain.base_entity import BaseEntity
from app.shared.domain.value_objects import UserRef
from app.utils.datetime import get_current_utc7_time

class ViolationType(str, Enum):
    LATE = "LATE"
    ABSENT = "ABSENT"
    OTHER = "OTHER"


class Violation(BaseEntity):
    """Domain entity representing a user violation."""

    reason: str = ""
    date: datetime | None = None
    user_id: int = 0

    # Embedded Value Objects — who is involved
    owner: UserRef | None = None  # user who was violated
    creator: UserRef | None = None  # who created this violation
    updater: UserRef | None = None  # who last updated this

    @field_validator("reason")
    @classmethod
    def reason_must_be_meaningful(cls, v: str) -> str:
        if not v or len(v.strip()) < 3:
            raise ValueError("Lý do vi phạm phải có ít nhất 3 ký tự")
        return v.strip()

    @field_validator("user_id")
    @classmethod
    def user_id_must_be_set(cls, v: int) -> int:
        if not v:
            raise ValueError("Phải chỉ định user_id")
        return v

    @classmethod
    def create_system_violation(
        cls,
        user_id: int,
        reason: str,
        date: datetime,
        system_user_id: int | None = None,
    ) -> "Violation":
        """Factory method for system-generated violations."""
        return cls(
            reason=reason,
            date=date,
            user_id=user_id,
            created_by=system_user_id,
            updated_by=system_user_id,
            created_at=get_current_utc7_time(),
            updated_at=get_current_utc7_time(),
        )

    @property
    def type(self) -> ViolationType:
        """Phân loại vi phạm dựa trên lý do (dùng cho thống kê/streak)."""
        r = self.reason.lower()
        if "trễ" in r:
            return ViolationType.LATE
        if "vắng" in r:
            return ViolationType.ABSENT
        return ViolationType.OTHER

