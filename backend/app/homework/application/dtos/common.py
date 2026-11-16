from pydantic import BaseModel


class HomeworkBase(BaseModel):
    title: str
    link: str | None = None
    slug: str | None = None
    requires_coding: bool = False
    requires_game: bool = False


class ExerciseSummaryDTO(BaseModel):
    """Thông tin tóm tắt của một bài tập coding con kèm số liệu hoàn thành."""

    exercise_id: str
    title: str
    order_index: int = 0
    completed_count: int = 0
    total_assigned: int = 0
    completion_rate: float = 0.0
