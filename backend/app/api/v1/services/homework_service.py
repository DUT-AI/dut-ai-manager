from app.models.homework_submission import HomeworkStatus
from app.models.homework_submission import HomeworkSubmission
from app.schemas.response import BadRequestException
from datetime import datetime
from typing import List, Optional

from app.core.context import get_current_user_id
from app.core.repository_factory import RepositoryFactory
from app.models import (
    Homework,
)
from app.schemas.homework import (
    HomeworkCreate,
    HomeworkUpdate,
)
from app.models.user import User, UserStatus


class HomeworkService:
    def __init__(self, repo_factory: RepositoryFactory):
        self.repo_factory = repo_factory

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Homework]:
        return self.repo_factory.homework.get_all(skip=skip, limit=limit)

    def get_assigned_to_user(self, skip: int = 0, limit: int = 100) -> List[Homework]:
        user_id = get_current_user_id()
        return self.repo_factory.homework.get_assigned_to_user(
            user_id, skip=skip, limit=limit
        )

    def get_by_id(self, homework_id: int) -> Optional[Homework]:
        return self.repo_factory.homework.get_by_id(homework_id)

    def create(self, data: HomeworkCreate) -> Homework:
        # Create homework model
        homework_data = data.model_dump(exclude={"assignee_ids"})
        homework = Homework(**homework_data)

        # Pass assignees to repo
        assignee_ids = data.assignee_ids
        if not assignee_ids:
            raise BadRequestException("Cần chọn người nhận")

        homework = self.repo_factory.homework.create_with_assignees(
            homework, assignee_ids
        )

        # Create submission for each assignee
        for assignee_id in assignee_ids:
            submission = HomeworkSubmission(
                homework_id=homework.id,
                assignee_id=assignee_id,
                status=HomeworkStatus.NOT_SUBMITTED,
                is_late=False,
                link="",
                created_by=assignee_id,
                updated_by=assignee_id,
            )
            self.repo_factory.homework_submission.create(submission)

        return homework

    def update(self, homework_id: int, data: HomeworkUpdate) -> Optional[Homework]:
        homework = self.get_by_id(homework_id)
        if not homework:
            return None

        update_data = data.model_dump(exclude_unset=True, exclude={"assignee_ids"})
        for key, value in update_data.items():
            setattr(homework, key, value)

        homework = self.repo_factory.homework.update(homework)

        # Update assignees if provided
        if data.assignee_ids is not None:
            self.repo_factory.homework.assign_users(homework_id, data.assignee_ids)
            # Refresh to get updated relationships if needed, but simple update return is enough

        return self.repo_factory.homework.get_by_id(homework_id)  # reload

    def delete(self, homework_id: int) -> bool:
        return self.repo_factory.homework.delete(homework_id)
