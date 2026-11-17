from abc import ABC, abstractmethod
from datetime import datetime

from app.homework.domain.entity import HomeworkSubmission, SubmissionType
from app.homework.domain.value_objects import (
    CodingSubmissionDetails,
    GameSubmissionDetails,
)


class HomeworkSubmissionRepositoryPort(ABC):
    """Cổng giao tiếp trừu tượng lưu trữ và truy xuất lịch sử nộp bài (Append-only Audit trail)."""

    @abstractmethod
    def add_submission(
        self, submission: HomeworkSubmission
    ) -> HomeworkSubmission:
        """Thêm mới một bản ghi lượt nộp bài."""
        ...

    @abstractmethod
    def update_submission(
        self,
        submission: HomeworkSubmission,
        submitted_at: datetime | None = None,
        is_passed: bool | None = None,
        exercise_id: str | None = None,
        exercise_title: str | None = None,
        score: float | None = None,
        attempt_number: int | None = None,
        details: CodingSubmissionDetails | GameSubmissionDetails | None = None,
        external_submission_id: str | None = None,
    ) -> HomeworkSubmission:
        """Cập nhật metadata/trạng thái của một bản ghi lượt nộp bài trùng khớp."""
        ...

    @abstractmethod
    def get_submissions_by_user(
        self, homework_id: int, user_id: int
    ) -> list[HomeworkSubmission]:
        """Lấy tất cả bài nộp của một học viên cho một bài tập cụ thể."""
        ...

    @abstractmethod
    def get_user_submissions_for_homeworks(
        self, homework_ids: list[int], user_id: int
    ) -> list[HomeworkSubmission]:
        """Lấy danh sách tất cả bài nộp của học viên trên nhiều bài tập."""
        ...

    @abstractmethod
    def get_all_submissions(self) -> list[HomeworkSubmission]:
        """Lấy toàn bộ lịch sử nộp bài trong hệ thống."""
        ...

    @abstractmethod
    def get_submissions_by_homework(
        self, homework_id: int
    ) -> list[HomeworkSubmission]:
        """Lấy tất cả bài nộp của một bài tập."""
        ...

    @abstractmethod
    def find_submission_match(
        self,
        homework_id: int,
        user_id: int,
        submission_type: SubmissionType,
        exercise_id: str | None = None,
        external_submission_id: str | None = None,
        submitted_at: datetime | None = None,
    ) -> HomeworkSubmission | None:
        """
        Tìm bản ghi lượt nộp trùng khớp phục vụ idempotent upsert (KHÔNG ghi đè lượt nộp khác):
        1. Ưu tiên khớp theo external_submission_id.
        2. Fallback khớp chính xác (homework_id, user_id, submission_type, exercise_id, submitted_at) khi thiếu ID.
        """
        ...
