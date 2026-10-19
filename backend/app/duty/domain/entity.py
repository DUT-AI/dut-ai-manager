"""
Duty Domain Entities & Enums.
"""

from datetime import date, datetime, time
from enum import Enum
from typing import Any
from pydantic import Field, field_validator

from app.shared.domain.base_entity import BaseEntity


class DutyStatus(str, Enum):
    PENDING = "PENDING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    VIOLATED = "VIOLATED"
    CANCELLED = "CANCELLED"


DEFAULT_DUTY_CHECKLIST = [
    {"id": "floor", "title": "Quét & lau sàn phòng", "checked": True},
    {"id": "tables", "title": "Lau bàn ghế học tập", "checked": True},
    {"id": "fans", "title": "Lau quạt bụi", "checked": False},
    {"id": "cabinets", "title": "Sắp xếp & lau tủ", "checked": False},
    {"id": "windows", "title": "Lau cửa kính & cửa ra vào", "checked": False},
]


class CleaningDuty(BaseEntity):
    """Domain Entity representing a Cleaning Duty task."""

    duty_date: date
    start_time: time | None = None
    end_time: time | None = None
    team_id: list[int] = Field(default_factory=list)
    team_name: str | None = None
    team_names: list[str] = Field(default_factory=list)
    meeting_id: int | None = None
    meeting_title: str | None = None

    status: DutyStatus = DutyStatus.PENDING

    @field_validator("team_id", mode="before")
    @classmethod
    def parse_team_id(cls, v: Any) -> list[int]:
        if isinstance(v, int):
            return [v]
        if isinstance(v, (list, tuple, set)):
            return [int(x) for x in v]
        if v is None:
            return []
        return [int(v)]

    # Toàn bộ nội dung công việc trực nhật hôm đó (mặc định + tạo thêm)
    checklist: list[dict] = Field(
        default_factory=lambda: [dict(item) for item in DEFAULT_DUTY_CHECKLIST]
    )

    # Note & Evidence
    note: str | None = None
    evidence_image_urls: list[str] = Field(default_factory=list)
    submitted_by: int | None = None
    submitted_by_name: str | None = None
    submitted_at: datetime | None = None

    # Approval & Rejection
    rejection_reason: str | None = None
    approved_by: int | None = None
    approved_at: datetime | None = None
    rejected_by: int | None = None
    rejected_at: datetime | None = None

    @property
    def has_at_least_one_task(self) -> bool:
        return any(
            bool(item.get("checked") or item.get("completed"))
            for item in (self.checklist or [])
        )

    def submit_evidence(
        self,
        submitted_by: int,
        image_urls: list[str],
        checklist: list[dict],
        note: str | None,
        submitted_at: datetime,
    ) -> None:
        """
        Submit duty evidence. Moves status to AWAITING_APPROVAL for Admin/HR review.
        """
        if not image_urls:
            raise ValueError("Vui lòng tải lên ít nhất 1 ảnh minh chứng thành phẩm")

        has_task = any(
            bool(item.get("checked") or item.get("completed"))
            for item in (checklist or [])
        )
        if not has_task:
            raise ValueError("Vui lòng tích chọn ít nhất 1 đầu việc trực nhật đã thực hiện")

        self.checklist = checklist
        self.note = note.strip() if note else None

        # Merge image urls if some exist
        combined = list(self.evidence_image_urls)
        for u in image_urls:
            if u not in combined:
                combined.append(u)
        self.evidence_image_urls = combined

        self.submitted_by = submitted_by
        self.submitted_at = submitted_at
        self.status = DutyStatus.AWAITING_APPROVAL
        self.rejection_reason = None

    def approve(self, approved_by: int, approved_at: datetime) -> None:
        """Admin or HR approves the duty evidence."""
        if self.status != DutyStatus.AWAITING_APPROVAL:
            raise ValueError("Chỉ có thể duyệt ca trực đang ở trạng thái chờ duyệt")
        self.status = DutyStatus.COMPLETED
        self.approved_by = approved_by
        self.approved_at = approved_at
        self.rejection_reason = None

    def reject(self, rejected_by: int, rejected_at: datetime, reason: str) -> None:
        """Admin or HR rejects the duty evidence with a reason."""
        if self.status != DutyStatus.AWAITING_APPROVAL:
            raise ValueError("Chỉ có thể từ chối ca trực đang ở trạng thái chờ duyệt")
        if not reason or not reason.strip():
            raise ValueError("Vui lòng nhập lý do từ chối để học viên khắc phục")
        self.status = DutyStatus.REJECTED
        self.rejected_by = rejected_by
        self.rejected_at = rejected_at
        self.rejection_reason = reason.strip()
