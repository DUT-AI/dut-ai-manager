from abc import ABC, abstractmethod
from datetime import datetime

from app.homework.domain.entity import Homework as HomeworkEntity


class HomeworkRepositoryPort(ABC):
    """Cổng giao tiếp trừu tượng lưu trữ và truy xuất thông tin bài tập (Homework)."""

    @abstractmethod
    def get_all(
        self,
        deleted: bool = False,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[HomeworkEntity]:
        """Lấy toàn bộ danh sách bài tập (có hỗ trợ limit/offset tùy chọn)."""
        ...

    @abstractmethod
    def get_paged(
        self, page: int = 1, page_size: int = 10, deleted: bool = False
    ) -> tuple[list[HomeworkEntity], int, dict[int, datetime | None]]:
        """Lấy danh sách bài tập phân trang kèm tổng số lượng và deadline tương ứng."""
        ...

    @abstractmethod
    def get_assigned_to_user_paged(
        self, user_id: int, page: int = 1, page_size: int = 10, deleted: bool = False
    ) -> tuple[list[HomeworkEntity], int, dict[int, datetime | None]]:
        """Lấy danh sách bài tập được giao cho một học viên theo phân trang."""
        ...

    @abstractmethod
    def get_all_assigned_to_user(
        self,
        user_id: int,
        deleted: bool = False,
        search: str | None = None,
    ) -> list[HomeworkEntity]:
        """Lấy toàn bộ danh sách bài tập được giao cho một học viên."""
        ...

    @abstractmethod
    def get_by_id(self, homework_id: int) -> HomeworkEntity | None:
        """Tìm bài tập theo ID."""
        ...

    @abstractmethod
    def get_by_slug(self, slug: str) -> HomeworkEntity | None:
        """Tìm bài tập theo slug."""
        ...

    @abstractmethod
    def create(self, homework: HomeworkEntity) -> HomeworkEntity:
        """Tạo mới một bài tập."""
        ...

    @abstractmethod
    def update(self, homework: HomeworkEntity) -> HomeworkEntity | None:
        """Cập nhật thông tin bài tập."""
        ...

    @abstractmethod
    def save(self, homework: HomeworkEntity) -> HomeworkEntity:
        """Lưu hoặc cập nhật bài tập (Upsert)."""
        ...

    @abstractmethod
    def delete(self, homework_id: int) -> bool:
        """Đánh dấu xóa mềm bài tập."""
        ...

    @abstractmethod
    def delete_by_id(self, homework_id: int) -> bool:
        """Xóa vĩnh viễn bài tập khỏi cơ sở dữ liệu."""
        ...
