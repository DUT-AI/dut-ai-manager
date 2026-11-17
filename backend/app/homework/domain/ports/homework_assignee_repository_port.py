from abc import ABC, abstractmethod
from datetime import date, datetime

from app.homework.domain.value_objects import (
    AssigneeUserInfo,
    DueHomeworkAssignment,
)


class HomeworkAssigneeRepositoryPort(ABC):
    """Cổng giao tiếp trừu tượng quản lý phân công học viên và hạn nộp cá nhân."""

    @abstractmethod
    def sync_assignees(
        self,
        homework_id: int,
        assignee_ids: list[int] | None,
        default_deadline: datetime | None = None,
        force_override: bool = False,
    ) -> None:
        """Đồng bộ danh sách học viên được giao bài tập."""
        ...

    @abstractmethod
    def assign_users(
        self,
        homework_id: int,
        user_ids: set[int] | list[int],
        deadline: datetime,
        force_override: bool = False,
    ) -> None:
        """Gán danh sách học viên vào bài tập kèm hạn nộp cụ thể."""
        ...

    @abstractmethod
    def get_user_deadline(
        self, homework_id: int, user_id: int
    ) -> datetime | None:
        """Lấy hạn nộp cá nhân của một học viên cho một bài tập."""
        ...

    @abstractmethod
    def update_deadline(
        self, homework_id: int, user_id: int, new_deadline: datetime
    ) -> bool:
        """Cập nhật hạn nộp cá nhân (hoãn bài tập)."""
        ...

    @abstractmethod
    def get_by_deadline_date(
        self, target_date: date
    ) -> list[DueHomeworkAssignment]:
        """Lấy danh sách các bài tập đến hạn trong ngày target_date theo giờ Việt Nam."""
        ...

    @abstractmethod
    def get_assigned_user_ids(self, homework_id: int) -> set[int]:
        """Lấy tập mã ID của tất cả học viên được giao bài tập."""
        ...

    @abstractmethod
    def get_assignees_with_user_info(
        self, homework_id: int
    ) -> list[AssigneeUserInfo]:
        """Lấy danh sách học viên kèm thông tin chi tiết người dùng và hạn nộp."""
        ...

    @abstractmethod
    def get_assigned_homework_ids(self, user_id: int) -> list[int]:
        """Lấy danh sách ID các bài tập được giao cho một học viên."""
        ...

    @abstractmethod
    def get_user_deadlines_for_homeworks(
        self, homework_ids: list[int], user_id: int
    ) -> dict[int, datetime]:
        """Lấy bản đồ hạn nộp của học viên cho danh sách bài tập."""
        ...

    @abstractmethod
    def get_min_deadlines_by_homework_ids(
        self, homework_ids: list[int]
    ) -> dict[int, datetime | None]:
        """Lấy hạn nộp sớm nhất của mỗi bài tập."""
        ...

    @abstractmethod
    def add_assignees(
        self, homework_id: int, user_ids: list[int], deadline: datetime
    ) -> None:
        """Thêm học viên vào bài tập."""
        ...

    @abstractmethod
    def remove_assignees(
        self, homework_id: int, user_ids: list[int]
    ) -> None:
        """Xóa học viên khỏi bài tập."""
        ...

    @abstractmethod
    def get_distinct_past_deadline_dates(
        self, before_date: date
    ) -> list[date]:
        """Lấy danh sách các ngày hạn nộp trong quá khứ."""
        ...
