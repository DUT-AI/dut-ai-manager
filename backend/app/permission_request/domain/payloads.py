from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.permission_request.domain.value_objects import RequestCategory


class BasePermissionPayload(BaseModel):
    """Base Value Object cho dữ liệu chuyên biệt của từng loại đơn."""

    model_config = ConfigDict(frozen=True, from_attributes=True)
    category: RequestCategory


class AbsencePayload(BasePermissionPayload):
    """Payload cho đơn xin vắng sinh hoạt (ABSENCE)."""

    category: Literal[RequestCategory.ABSENCE] = RequestCategory.ABSENCE
    meeting_id: int | None = None


class LatePayload(BasePermissionPayload):
    """Payload cho đơn xin đi trễ sinh hoạt (LATE)."""

    category: Literal[RequestCategory.LATE] = RequestCategory.LATE
    meeting_id: int | None = None
    start_time: datetime | None = None


class PostponePayload(BasePermissionPayload):
    """Payload cho đơn xin hoãn nộp bài tập (POSTPONE)."""

    category: Literal[RequestCategory.POSTPONE] = RequestCategory.POSTPONE
    homework_id: int | None = None
    start_time: datetime | None = None


class ChangeMeetingPayload(BasePermissionPayload):
    """Payload cho đơn xin đổi buổi sinh hoạt (CHANGE_MEETING)."""

    category: Literal[RequestCategory.CHANGE_MEETING] = RequestCategory.CHANGE_MEETING
    meeting_id: int | None = None
    old_meeting_id: int | None = None
    start_time: datetime | None = None


class OtherPayload(BasePermissionPayload):
    """Payload cho đơn loại khác (OTHER)."""

    category: Literal[RequestCategory.OTHER] = RequestCategory.OTHER


# Discriminated Union cho việc parse tự động từ dict/JSON
PermissionPayloadUnion = Annotated[
    AbsencePayload
    | LatePayload
    | PostponePayload
    | ChangeMeetingPayload
    | OtherPayload,
    Field(discriminator="category"),
]
