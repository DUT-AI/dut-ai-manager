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
        assignee_ids = sorted(
            list(self.homework_assignee_repo.get_assigned_user_ids(homework_id))
        )
        return HomeworkResponseDetail.from_domain(hw, assignee_ids=assignee_ids)
