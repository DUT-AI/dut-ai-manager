from app.api.v1.services.violation_service import ViolationService
from app.api.v1.services.user_service import UserService
from typing import List, Optional

from fastapi import UploadFile

from app.core.context import get_current_user_id
from app.core.minio_service import MinioService
from app.core.repository_factory import RepositoryFactory
from app.models import HomeworkSubmission, User
from app.models.homework_submission import HomeworkStatus
from app.models.role import Role, RoleType
from app.schemas.activity import ViolationCreate
from app.schemas.response import BadRequestException
from app.utils.datetime import get_current_utc7_time
from loguru import logger


class HomeworkSubmissionService:
    def __init__(
        self,
        repo_factory: RepositoryFactory,
        violation_service: ViolationService,
        user_service: UserService,
        minio_service: MinioService,
    ):
        self.repo_factory = repo_factory
        self.violation_service = violation_service
        self.user_service = user_service
        self.minio_service = minio_service

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
            case RoleType.ADMIN.value:
                return homework_submissions
            case RoleType.LEADER.value:
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
            case RoleType.TEAMMATE.value:
                # Chỉ có thể xem của mình
                filter_submissions = [
                    item
                    for item in homework_submissions
                    if item.owner_id == current_user.id
                ]
                return filter_submissions
            case _:
                return []

    async def submit(self, homework_id: int, file: UploadFile) -> HomeworkSubmission:
        """Submit homework by uploading a file to MinIO."""
        # Validate file
        file_content = await file.read()
        file_size = len(file_content)

        validation_error = self.minio_service.validate_file(
            file.filename or "", file_size
        )
        if validation_error:
            raise BadRequestException(validation_error)

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
            await self.violation_service.create(
                ViolationCreate(
                    user_id=user_id,
                    reason=f"Nộp bài trễ: {homework.title}",
                    date=now_utc7,
                ),
                is_system=True,
            )

        # Upload file to MinIO
        # Format: homework_title/username_filename_timestamp.ext
        # Use owner from existing submission if available to avoid extra query
        if existing_submission and existing_submission.owner:
            user = existing_submission.owner
        else:
            user = self.user_service.get_by_id(user_id)
        user_name = user.name.replace(" ", "_") if user else f"user_{user_id}"
        homework_title = homework.title.replace(" ", "_").replace("/", "_")
        timestamp = now_utc7.strftime("%Y%m%d_%H%M%S")

        # Get filename and extension
        original_filename = (
            file.filename.replace(" ", "_") if file.filename else "submission.zip"
        )
        if "." in original_filename:
            name_part, ext_part = original_filename.rsplit(".", 1)
            safe_filename = f"{name_part}_{timestamp}.{ext_part}"
        else:
            safe_filename = f"{original_filename}_{timestamp}"

        object_name = (
            f"homework-submissions/{homework_title}/{user_name}_{safe_filename}"
        )

        file_url = self.minio_service.upload_file(
            file_data=file_content,
            filename=object_name,
            content_type=file.content_type or "application/octet-stream",
        )

        if existing_submission:
            existing_submission.link = file_url
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
            link=file_url,
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
            case RoleType.ADMIN.value:
                # Admin can update any status
                pass
            case RoleType.LEADER.value:
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
                if submission.owner_id not in team_member_ids:
                    raise BadRequestException(
                        "Bạn chỉ có thể update submission của thành viên cùng team"
                    )
            case _:
                raise BadRequestException("Bạn không có quyền thực hiện hành động này")

        submission.status = status
        return self.repo_factory.homework_submission.update(submission)
