from datetime import datetime

from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.homework_assignee_repository import (
    HomeworkAssigneeRepository,
)
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.shared.application.query_support_utils import build_query_support


class GetHomeworksPagedUseCase:
    """Use case lấy danh sách bài tập có phân trang phục vụ trang quản trị kèm hạn nộp."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
    ):
        self.homework_repo = homework_repo
        self.homework_assignee_repo = homework_assignee_repo

    def execute(
        self, page: int = 1, page_size: int = 20, deleted: bool = False
    ) -> tuple[list[HomeworkEntity], int, dict[int, datetime]]:
        qs = build_query_support(
            page=page, page_size=page_size, sort_by="created_at", descending=True
        )
        homeworks, total = self.homework_repo.get_paged(
            query_support=qs, deleted=deleted, page=page, page_size=page_size
        )
        hw_ids = [h.id for h in homeworks if h.id]
        deadlines = self.homework_assignee_repo.get_min_deadlines_by_homework_ids(
            hw_ids
        )
        return homeworks, total, deadlines
