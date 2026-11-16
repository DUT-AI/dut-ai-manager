from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.homework.application.dtos.common import ExerciseSummaryDTO, HomeworkBase
from app.homework.domain.entity import Homework
from app.shared.domain.datetime_types import UtcDateTime


class HomeworkCreate(HomeworkBase):
    deadline: UtcDateTime
    assignee_ids: list[int] = Field(default_factory=list)


class HomeworkUpdate(BaseModel):
    title: str | None = None
    deadline: UtcDateTime | None = None
    link: str | None = None
    slug: str | None = None
    requires_coding: bool | None = None
    requires_game: bool | None = None
    assignee_ids: list[int] | None = None
    force_override_deadlines: bool = False


class HomeworkResponse(HomeworkBase):
    id: int
    deadline: datetime | None = None
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    # Computed fields (populated by use cases)
    submission_count: int = 0
    is_submitted: bool | None = None
    is_overdue: bool | None = None
    has_coding: bool = False
    coding_submitted: bool = False
    has_game: bool = False
    game_submitted: bool = False
    uncompleted_items: list[str] = Field(default_factory=list)
    coding_status: str = "NOT_SUBMITTED"
    total_coding_required: int = 0
    total_coding_completed: int = 0

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(
        cls, hw: Homework, deadline: datetime | None = None
    ) -> "HomeworkResponse":
        return cls(
            id=hw.id,
            title=hw.title,
            deadline=deadline,
            link=hw.link,
            slug=hw.slug,
            requires_coding=hw.requires_coding,
            requires_game=hw.requires_game,
            created_at=hw.created_at,
            updated_at=hw.updated_at,
            created_by=hw.created_by,
        )

    from_entity = from_domain


class HomeworkResponseDetail(HomeworkResponse):
    """DTO chi tiết bài tập bao gồm danh sách assignee_ids phục vụ màn hình chỉnh sửa/chi tiết."""

    assignee_ids: list[int] = Field(default_factory=list)
    coding_exercises: list[ExerciseSummaryDTO] = Field(default_factory=list)

    @classmethod
    def from_domain(
        cls,
        hw: Homework,
        assignee_ids: list[int] | None = None,
        deadline: datetime | None = None,
        coding_exercises: list[ExerciseSummaryDTO] | None = None,
    ) -> "HomeworkResponseDetail":
        return cls(
            id=hw.id,
            title=hw.title,
            deadline=deadline,
            link=hw.link,
            slug=hw.slug,
            requires_coding=hw.requires_coding,
            requires_game=hw.requires_game,
            created_at=hw.created_at,
            updated_at=hw.updated_at,
            created_by=hw.created_by,
            assignee_ids=assignee_ids or [],
            coding_exercises=coding_exercises or [],
        )

    from_entity = from_domain


class SyncHomeworkResult(BaseModel):
    """Kết quả phản hồi chi tiết sau khi đồng bộ bài tập từ Quiz API."""

    homework_id: int
    title: str
    requires_coding: bool
    requires_game: bool
    coding_exercises_count: int = 0
    game_questions_count: int = 0
    synced_coding_count: int = 0
    updated_coding_count: int = 0
    synced_game_count: int = 0
    updated_game_count: int = 0
    message: str

    model_config = ConfigDict(from_attributes=True)
