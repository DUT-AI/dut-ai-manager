from app.api.v1.services.user_service import UserService
from typing import List, Optional

from app.api.v1.services.violation_service import ViolationService
from app.core.context import get_current_user_id
from app.core.repository_factory import RepositoryFactory
from app.models import HomeworkSubmission, User
from app.models.homework_submission import HomeworkStatus
from app.models.role import Role, RoleType
from app.schemas.activity import ViolationCreate
from app.schemas.homework import HomeworkSubmissionCreate
from app.schemas.response import BadRequestException
from app.utils.datetime import get_current_utc7_time
from loguru import logger


class HomeworkSubmissionService:
    def __init__(
        self,
        repo_factory: RepositoryFactory,
        violation_service: ViolationService,
        user_service: UserService,
    ):
        self.repo_factory = repo_factory
        self.violation_service = violation_service
        self.user_service = user_service

    def get_submission_of_user(
        self,
        homework_id: int,
    ) -> Optional[HomeworkSubmission]:
        user_id = get_current_user_id()
        return self.repo_factory.homework_submission.get_by_homework_and_user(
            homework_id, user_id
        )

    def get_all_by_homework(
        self, homework_id: int, current_user: User
    ) -> List[HomeworkSubmission]:
        homework_submissions = (
            self.repo_factory.homework_submission.get_all_by_homework(homework_id)
        )
        logger.debug(homework_submissions)
        match current_user.role.name:
            case RoleType.ADMIN:
                return homework_submissions
            case RoleType.LEADER:
                # Lấy tất cả member_ids của các team mà leader thuộc về
                team_member_ids = set(
                    member.user_id
                    for tm in current_user.team_members  # các team mà leader thuộc về
                    for member in tm.team.team_members  # các member của mỗi team
                )
                logger.debug(f"Team member IDs: {team_member_ids}")
                filter_submissions = [
                    item
                    for item in homework_submissions
                    if item.owner_id in team_member_ids
                ]
                return filter_submissions
            case RoleType.TEAMMATE:
                # Chỉ có thể xem của mình
                filter_submissions = [
                    item
                    for item in homework_submissions
                    if item.owner_id == current_user.id
                ]
                return filter_submissions
            case _:
                return []

    def submit(
        self, homework_id: int, data: HomeworkSubmissionCreate
    ) -> HomeworkSubmission:
        # Check if submission exists
        existing_submission = self.get_submission_of_user(homework_id)

        # Get homework info
        homework = self.repo_factory.homework.get_by_id(homework_id)
        if not homework:
            raise BadRequestException("Không tồn tại homework này")

        # Current time in UTC+7
        now_utc7 = get_current_utc7_time()

        # Check deadline
        is_late = now_utc7 > homework.deadline

        user_id = get_current_user_id()

        # If late and not late before, create violation via ViolationService
        if is_late and (not existing_submission or not existing_submission.is_late):
            self.violation_service.create(
                ViolationCreate(
                    user_id=user_id,
                    reason=f"Nộp bài trễ: {homework.title}",
                    date=now_utc7,
                ),
                is_system=True,
            )

        if existing_submission:
            existing_submission.link = str(data.link)
            existing_submission.status = HomeworkStatus.SUBMITTED
            existing_submission.is_late = is_late
            existing_submission.updated_at = now_utc7
            existing_submission.updated_by = user_id
            return self.repo_factory.homework_submission.update(existing_submission)

        # Should not happen as we pre-create submissions
        system_user = self.user_service.get_system()
        submission = HomeworkSubmission(
            homework_id=homework_id,
            owner_id=user_id,
            link=str(data.link),
            status=HomeworkStatus.SUBMITTED,
            is_late=is_late,
            created_by=system_user.id,
            updated_by=system_user.id,
        )
        return self.repo_factory.homework_submission.create(submission)

    def update_status(
        self,
        submission_id: int,
        status: HomeworkStatus,
        current_user: User,
    ) -> Optional[HomeworkSubmission]:
        submission = self.repo_factory.homework_submission.get_by_id(submission_id)
        if not submission:
            raise BadRequestException("Không tồn tại submission này")

        if submission.status == HomeworkStatus.FINISHED:
            raise BadRequestException("Submission đã được đánh dấu 'finish'")

        if submission.status == HomeworkStatus.NOT_SUBMITTED:
            raise BadRequestException("Submission chưa được nộp, không được check")

        # Authorization logic based on role
        match current_user.role.name:
            case RoleType.ADMIN:
                # Admin can update any status
                pass
            case RoleType.LEADER:
                if submission.status == HomeworkStatus.LEADER_CHECKED:
                    raise BadRequestException(
                        "Submission đã được đánh dấu 'leader đã check'"
                    )

                # Leader can only set status to "leader đã check"
                if status != HomeworkStatus.LEADER_CHECKED:
                    raise BadRequestException(
                        "Leader chỉ có thể đánh dấu 'leader đã check'"
                    )

                # Leader can only update submissions of same team members
                team_member_ids = set(
                    member.user_id
                    for tm in current_user.team_members
                    for member in tm.team.team_members
                )
                if submission.created_by not in team_member_ids:
                    raise BadRequestException(
                        "Bạn chỉ có thể update submission của thành viên cùng team"
                    )
            case _:
                raise BadRequestException("Bạn không có quyền thực hiện hành động này")

        submission.status = status
        return self.repo_factory.homework_submission.update(submission)
