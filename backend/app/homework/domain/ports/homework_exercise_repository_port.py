from abc import ABC, abstractmethod

from app.homework.domain.entity import HomeworkExercise


class HomeworkExerciseRepositoryPort(ABC):
    """Cổng giao tiếp quản lý danh mục bài tập lập trình con chính thức của từng bài tập."""

    @abstractmethod
    def get_active_by_homework(self, homework_id: int) -> list[HomeworkExercise]:
        """Lấy danh sách các bài tập con đang hiệu lực của một bài tập, sắp theo order_index."""
        ...

    @abstractmethod
    def get_active_by_homework_ids(
        self, homework_ids: list[int]
    ) -> dict[int, list[HomeworkExercise]]:
        """Lấy bản đồ danh sách bài tập con đang hiệu lực theo nhiều homework_id."""
        ...

    @abstractmethod
    def sync_exercises(
        self, homework_id: int, exercises: list[HomeworkExercise]
    ) -> list[HomeworkExercise]:
        """
        Đồng bộ danh mục bài tập con chính thức cho một bài tập:
        - Upsert (tạo mới hoặc cập nhật title, order_index, is_active=True) theo exercise_id.
        - Đặt is_active=False cho các bài tập con cũ không còn trong danh sách mới.
        """
        ...
