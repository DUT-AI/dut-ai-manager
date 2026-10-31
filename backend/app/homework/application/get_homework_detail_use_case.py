from app.homework.application.dtos import HomeworkResponseDetail
from app.homework.infrastructure.homework_assignee_repository import (
    HomeworkAssigneeRepository,
)
from app.homework.infrastructure.homework_repository import HomeworkRepository


class GetHomeworkDetailUseCase:
    """Use case lấy thông tin chi tiết một bài tập theo ID bao gồm danh sách assignee_ids."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
    ):
        self.homework_repo = homework_repo
        self.homework_assignee_repo = homework_assignee_repo

    def execute(self, homework_id: int) -> HomeworkResponseDetail | None:
        hw = self.homework_repo.get_by_id(homework_id)
        if not hw:
            return None
        assignees = self.homework_assignee_repo.get_assignees_with_user_info(
            homework_id
        )
        assignee_ids = sorted([a.user_id for a in assignees])
        deadlines = [a.deadline for a in assignees if a.deadline]
        min_dl = min(deadlines) if deadlines else None
        return HomeworkResponseDetail.from_domain(
            hw, assignee_ids=assignee_ids, deadline=min_dl
        )
