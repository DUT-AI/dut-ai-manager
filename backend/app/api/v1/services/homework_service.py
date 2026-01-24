from app.api.v1.services.notification_service import NotificationService
from app.models.homework_submission import HomeworkStatus
from app.models.homework_submission import HomeworkSubmission
from app.schemas.response import BadRequestException
from typing import List, Optional, Set

from app.core.repository_factory import RepositoryFactory
from app.models import Homework
from app.schemas.homework import HomeworkCreate, HomeworkUpdate


class HomeworkService:
    def __init__(
        self,
        repo_factory: RepositoryFactory,
        notification_service: NotificationService,
    ):
        self.repo_factory = repo_factory
        self.notification_service = notification_service

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Homework]:
        return self.repo_factory.homework.get_all(skip=skip, limit=limit)

    def get_assigned_to_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Homework]:
        return self.repo_factory.homework.get_assigned_to_user(
            user_id, skip=skip, limit=limit
        )

    def get_by_id(self, homework_id: int) -> Optional[Homework]:
        return self.repo_factory.homework.get_by_id(homework_id)

    def _collect_assignee_ids(
        self, assignee_ids: Optional[List[int]], team_ids: Optional[List[int]]
    ) -> Set[int]:
        """Collect all unique assignee IDs from direct IDs and team members"""
        all_ids: Set[int] = set()

        if assignee_ids:
            all_ids.update(assignee_ids)

        if team_ids:
            team_user_ids = self.repo_factory.team.get_user_ids_by_teams(team_ids)
            all_ids.update(team_user_ids)

        return all_ids

    async def create(self, data: HomeworkCreate) -> Homework:
        # Collect all assignee IDs
        all_assignee_ids = self._collect_assignee_ids(data.assignee_ids, data.team_ids)

        if not all_assignee_ids:
            raise BadRequestException("Cần chọn người nhận hoặc team")

        # Create homework model
        homework_data = data.model_dump(exclude={"assignee_ids", "team_ids"})
        homework = Homework(**homework_data)
        homework = self.repo_factory.homework.create(homework)

        # Create submission for each assignee
        for owner_id in all_assignee_ids:
            submission = HomeworkSubmission(
                homework_id=homework.id,
                owner_id=owner_id,
                status=HomeworkStatus.NOT_SUBMITTED,
                is_late=False,
                link="",
            )
            self.repo_factory.homework_submission.create(submission)

        # Send notifications asynchronously
        for user_id in all_assignee_ids:
            user = self.repo_factory.user.get_by_id(user_id)
            if user:
                # We don't await each notification to avoid blocking the response
                # But since the request is async, we can await it or use background tasks
                # For simplicity and reliability in this agentic task, we await it here
                await self.notification_service.send_homework_assigned_notification(
                    user, homework
                )

        return homework

    async def update(
        self, homework_id: int, data: HomeworkUpdate
    ) -> Optional[Homework]:
        homework = self.get_by_id(homework_id)
        if not homework:
            return None

        # Update homework fields
        update_data = data.model_dump(
            exclude_unset=True, exclude={"assignee_ids", "team_ids"}
        )
        for key, value in update_data.items():
            setattr(homework, key, value)
        homework = self.repo_factory.homework.update(homework)

        # Sync assignees if provided
        if data.assignee_ids is not None or data.team_ids is not None:
            new_assignee_ids = self._collect_assignee_ids(
                data.assignee_ids, data.team_ids
            )

            if new_assignee_ids:
                # Get current assignees
                current_ids = set(
                    self.repo_factory.homework_submission.get_owner_ids_by_homework(
                        homework_id
                    )
                )

                # Add new assignees
                to_add = new_assignee_ids - current_ids
                for owner_id in to_add:
                    submission = HomeworkSubmission(
                        homework_id=homework_id,
                        owner_id=owner_id,
                        status=HomeworkStatus.NOT_SUBMITTED,
                        is_late=False,
                        link="",
                    )
                    self.repo_factory.homework_submission.create(submission)

                    # Send notification to new assignee
                    user = self.repo_factory.user.get_by_id(owner_id)
                    if user:
                        await self.notification_service.send_homework_assigned_notification(
                            user, homework
                        )

                # Remove old assignees
                to_remove = current_ids - new_assignee_ids
                for owner_id in to_remove:
                    self.repo_factory.homework_submission.delete_by_homework_and_owner(
                        homework_id, owner_id
                    )

        return self.repo_factory.homework.get_by_id(homework_id)

    def delete(self, homework_id: int) -> bool:
        # Delete all submissions first
        submissions = self.repo_factory.homework_submission.get_all_by_homework(
            homework_id
        )
        for submission in submissions:
            self.repo_factory.homework_submission.delete(submission)

        return self.repo_factory.homework.delete_by_id(homework_id)
