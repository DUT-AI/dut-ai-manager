"""
Duty DTOs (Data Transfer Objects).
"""

from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class DutyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    duty_date: date
    start_time: time | None = None
    end_time: time | None = None
    team_id: list[int] = []
    team_name: str | None = None
    team_names: list[str] = []
    meeting_id: int | None = None
    meeting_title: str | None = None
    status: str

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
    checklist: list[dict] = []

    # Note & Evidence
    note: str | None = None
    evidence_image_urls: list[str] = []
    submitted_by: int | None = None
    submitted_by_name: str | None = None
    submitted_at: datetime | None = None

    # Approval & Rejection
    rejection_reason: str | None = None
    approved_by: int | None = None
    approved_at: datetime | None = None
    rejected_by: int | None = None
    rejected_at: datetime | None = None


class ToggleDutyScheduleRequest(BaseModel):
    duty_date: date
    team_id: int | list[int]
    enabled: bool
    start_time: time | None = None
    end_time: time | None = None
    meeting_id: int | None = None
    checklist: list[dict] | None = None
    note: str | None = None


class BatchCreateDutyRequest(BaseModel):
    team_ids: list[int]
    duty_date: date
    start_time: time | None = None
    end_time: time | None = None
    checklist: list[dict] | None = None
    note: str | None = None


class UpdateDutyRequest(BaseModel):
    checklist: list[dict] | None = None
    note: str | None = None
    duty_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    team_id: int | list[int] | None = None


class RejectDutyRequest(BaseModel):
    reason: str


class WeeklyDutyClassDto(BaseModel):
    team_id: list[int] = []
    team_name: str
    team_names: list[str] = []

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

    day_of_week: int  # 1: Thứ 2, 2: Thứ 3, ..., 6: Thứ 7, 7: CN
    day_name: str  # "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 7"
    duty_date: date
    start_time: time | None = None
    end_time: time | None = None
    is_time_conflict: bool = False
    conflict_message: str | None = None
    is_scheduled: bool
    duty_id: int | None = None
    status: str | None = None
    has_meeting: bool = False
    meeting_id: int | None = None
    meeting_title: str | None = None
    meeting_time: str | None = None
    evidence_image_urls: list[str] = []
    note: str | None = None
    checklist: list[dict] = []
    submitted_by_name: str | None = None
    rejection_reason: str | None = None
