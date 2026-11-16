from abc import ABC, abstractmethod
from datetime import datetime

from app.homework.domain.entity import HomeworkSubmission, SubmissionType
from app.homework.domain.value_objects import (
    CodingSubmissionDetails,
    GameSubmissionDetails,
)


class HomeworkSubmissionRepositoryPort(ABC):
    """Cổng giao tiếp trừu tượng lưu trữ và truy xuất lịch sử nộp bài (Audit trail)."""

    @abstractmethod
    def add_submission(
        self, submission: HomeworkSubmission
    ) -> HomeworkSubmission:
        """Thêm mới một bản ghi bài nộp."""
        ...

    @abstractmethod
    def update_submission(
        self,
        submission: HomeworkSubmission,
        submitted_at: datetime,
        is_passed: bool,
        exercise_id: str | None = None,
        exercise_title: str | None = None,
        score: float | None = None,
        attempt_number: int = 1,
        details: CodingSubmissionDetails | GameSubmissionDetails | None = None,
    ) -> HomeworkSubmission:
        """Cập nhật bản ghi bài nộp đã có."""
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
    ) -> dict[int, list[HomeworkSubmission]]:
        """Lấy bài nộp của học viên gom nhóm theo từng bài tập."""
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
        quiz_submission_id: str | None = None,
        submitted_at: datetime | None = None,
    ) -> HomeworkSubmission | None:
        """Tìm bản ghi bài nộp trùng khớp để thực hiện idempotent update."""
        ...

    @abstractmethod
    def get_submissions_by_exercise(
        self, homework_id: int, exercise_id: str
    ) -> list[HomeworkSubmission]:
        """Lấy danh sách nộp bài cho một bài tập coding con cụ thể."""
        ...

    @abstractmethod
    def get_submitted_exercise_ids(
        self, homework_id: int, user_id: int
    ) -> set[str]:
        """Lấy tập mã các bài tập coding con mà học viên đã nộp."""
        ...

    @abstractmethod
    def get_required_exercise_ids_map(
        self, homework_ids: list[int]
    ) -> dict[int, set[str]]:
        """Lấy bản đồ tập các bài tập con bắt buộc của nhiều bài tập."""
        ...
