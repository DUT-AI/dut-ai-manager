from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.shared.application.query_support_utils import build_query_support


class GetHomeworksPagedUseCase:
    """Use case lấy danh sách bài tập có phân trang phục vụ trang quản trị."""

    def __init__(self, homework_repo: HomeworkRepository):
        self.homework_repo = homework_repo

    def execute(
        self, page: int = 1, page_size: int = 20, deleted: bool = False
    ) -> tuple[list[HomeworkEntity], int]:
        qs = build_query_support(
            page=page, page_size=page_size, sort_by="created_at", descending=True
        )
        return self.homework_repo.get_paged(
            query_support=qs, deleted=deleted, page=page, page_size=page_size
        )
