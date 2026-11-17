from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.homework.application.dtos.common import ExerciseSummaryDTO, HomeworkBase
from app.homework.application.dtos.submission_dtos import (
    HomeworkSubmissionDetailResponse,
    MyHomeworkExerciseStatusDTO,
)
from app.homework.domain.entity import Homework
from app.homework.domain.value_objects import (
    CompletionStatus,
    SubmissionEvaluation,
    TimelinessStatus,
)
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
    last_synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    # Computed SSOT 2-dimensional evaluation fields
    submission_count: int = 0
    completion_status: CompletionStatus = CompletionStatus.NOT_STARTED
    timeliness_status: TimelinessStatus = TimelinessStatus.UPCOMING
    completed_at: datetime | None = None
    is_submitted: bool | None = None
    is_late: bool = False
    is_overdue: bool | None = None

    has_coding: bool = False
    coding_submitted: bool = False
    coding_is_late: bool = False
    coding_status: str = "NOT_SUBMITTED"
    total_coding_required: int = 0
    total_coding_completed: int = 0

    has_game: bool = False
    game_submitted: bool = False
    game_is_late: bool = False
    uncompleted_items: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(
        cls, hw: Homework, deadline: datetime | None = None
    ) -> "HomeworkResponse":
        assert hw.id is not None
        return cls(
            id=hw.id,
            title=hw.title,
            deadline=deadline,
            link=hw.link,
            slug=hw.slug,
            requires_coding=hw.requires_coding,
            requires_game=hw.requires_game,
            last_synced_at=hw.last_synced_at,
            created_at=hw.created_at,
            updated_at=hw.updated_at,
            created_by=hw.created_by,
            has_coding=hw.requires_coding,
            has_game=hw.requires_game,
        )

    from_entity = from_domain

    @classmethod
    def from_evaluation(
        cls,
        hw: Homework,
        evaluation: SubmissionEvaluation,
        deadline: datetime | None = None,
    ) -> "HomeworkResponse":
        assert hw.id is not None
        return cls(
            id=hw.id,
            title=hw.title,
            deadline=deadline,
            link=hw.link,
            slug=hw.slug,
            requires_coding=hw.requires_coding,
            requires_game=hw.requires_game,
            last_synced_at=hw.last_synced_at,
            created_at=hw.created_at,
            updated_at=hw.updated_at,
            created_by=hw.created_by,
            completion_status=evaluation.completion_status,
            timeliness_status=evaluation.timeliness_status,
            completed_at=evaluation.completed_at,
            is_submitted=evaluation.is_submitted,
            is_late=evaluation.is_late,
            is_overdue=evaluation.is_overdue,
            has_coding=hw.requires_coding,
            coding_submitted=evaluation.coding_submitted,
            coding_is_late=evaluation.coding_is_late,
            coding_status=evaluation.coding_status,
            total_coding_required=evaluation.total_coding_required,
            total_coding_completed=evaluation.total_coding_completed,
            has_game=hw.requires_game,
            game_submitted=evaluation.game_submitted,
            game_is_late=evaluation.game_is_late,
            uncompleted_items=evaluation.uncompleted_items,
        )


class HomeworkResponseDetail(HomeworkResponse):
    """DTO chi tiết bài tập phục vụ màn hình quản trị chỉnh sửa/chi tiết."""

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
        assert hw.id is not None
        return cls(
            id=hw.id,
            title=hw.title,
            deadline=deadline,
            link=hw.link,
            slug=hw.slug,
            requires_coding=hw.requires_coding,
            requires_game=hw.requires_game,
            last_synced_at=hw.last_synced_at,
            created_at=hw.created_at,
            updated_at=hw.updated_at,
            created_by=hw.created_by,
            has_coding=hw.requires_coding,
            has_game=hw.requires_game,
            assignee_ids=assignee_ids or [],
            coding_exercises=coding_exercises or [],
        )

    from_entity = from_domain


class MyHomeworksStats(BaseModel):
    """Thống kê tổng quan trên 100% bài tập được giao của học viên."""

    total: int = 0
    completed: int = 0
    completed_on_time: int = 0
    completed_late: int = 0
    uncompleted: int = 0
    overdue: int = 0


class MyHomeworksPageResponse(BaseModel):
    """Phản hồi chuẩn cho trang Bài tập của tôi (Server-driven filter/search/pagination + tổng stats)."""

    items: list[HomeworkResponse] = Field(default_factory=list)
    stats: MyHomeworksStats = Field(default_factory=MyHomeworksStats)


class MyHomeworkDetailResponse(BaseModel):
    """Phản hồi chi tiết bài tập cá nhân của học viên kèm hạn nộp cá nhân và tiến độ từng bài con."""

    homework: HomeworkResponse
    coding_exercises: list[MyHomeworkExerciseStatusDTO] = Field(default_factory=list)
    submissions: list[HomeworkSubmissionDetailResponse] = Field(default_factory=list)


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
    last_synced_at: datetime | None = None
    message: str

    model_config = ConfigDict(from_attributes=True)


class SyncMyHomeworksResult(BaseModel):
    """Kết quả đồng bộ nhanh các bài chưa hoàn thành của học viên hiện tại."""

    total_checked: int = 0
    synced_count: int = 0
    failed_count: int = 0
    results: list[SyncHomeworkResult] = Field(default_factory=list)
    failed_homework_ids: list[int] = Field(default_factory=list)


class BackfillFailedItem(BaseModel):
    """Thông tin một bài tập thất bại trong quá trình backfill danh mục bài con."""

    homework_id: int
    title: str
    error: str


class BackfillHomeworkExercisesResult(BaseModel):
    """Kết quả chuẩn hóa dữ liệu danh mục bài con cho toàn bộ bài tập hiện có."""

    total_homeworks: int = 0
    succeeded: int = 0
    skipped_no_slug: int = 0
    failed: int = 0
    failed_details: list[BackfillFailedItem] = Field(default_factory=list)
