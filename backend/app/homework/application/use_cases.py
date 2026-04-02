from typing import List, Optional, Set

from app.core.context import get_current_user_id
from app.homework.application.dtos import HomeworkCreate, HomeworkUpdate
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.domain.entity import HomeworkSubmission as HomeworkSubmissionEntity
from app.homework.domain.value_objects import (
    HomeworkAssigned,
    HomeworkStatus,
    HomeworkSubmitted,
)
from app.homework.infrastructure.repository import (
    HomeworkRepository,
    HomeworkSubmissionRepository,
)
from app.rbac.domain.entity import RoleType
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import EventBus
from app.shared.infrastructure.minio_service import MinioService
from app.team.infrastructure.repository import TeamRepository
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time
from fastapi import UploadFile


class HomeworkUseCases:
    def __init__(
        self,
        homework_repo: HomeworkRepository,
        submission_repo: HomeworkSubmissionRepository,
        user_repo: UserRepository,
        team_repo: TeamRepository,
        minio_service: MinioService,
    ):
        self.homework_repo = homework_repo
        self.submission_repo = submission_repo
        self.user_repo = user_repo
        self.team_repo = team_repo
        self.minio_service = minio_service

    async def _handle_file(self, file: UploadFile, title: str) -> str:
        content = await file.read()
        error = self.minio_service.validate_file(file.filename, len(content))
        if error:
            raise BadRequestException(error)

        now_utc7 = get_current_utc7_time()
        timestamp = now_utc7.strftime("%Y%m%d_%H%M%S")
        filename = f"{self.minio_service.HOMEWORK_PREFIX}/{title}/{title}_{timestamp}"

        file_url = self.minio_service.upload_file(content, filename, file.content_type)
        return file_url

    def get_all(
        self, skip: int = 0, limit: int = 100, deleted: bool = False
    ) -> List[HomeworkEntity]:
        return self.homework_repo.get_all(skip=skip, limit=limit, deleted=deleted)

    def get_assigned_to_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[HomeworkEntity]:
        return self.homework_repo.get_assigned_to_user(user_id, skip=skip, limit=limit)

    def get_by_id(self, homework_id: int) -> Optional[HomeworkEntity]:
        return self.homework_repo.get_by_id(homework_id)

    def _collect_assignee_ids(
        self, assignee_ids: Optional[List[int]], team_ids: Optional[List[int]]
    ) -> Set[int]:
        all_ids: Set[int] = set()

        if assignee_ids:
            all_ids.update(assignee_ids)

        if team_ids:
            team_user_ids = self.team_repo.get_user_ids_by_teams(team_ids)
            all_ids.update(team_user_ids)

        return all_ids

    async def create(self, data: HomeworkCreate, file: UploadFile) -> HomeworkEntity:
        file_url = None
        if file:
            file_url = await self._handle_file(file, data.title)

        all_assignee_ids = self._collect_assignee_ids(data.assignee_ids, data.team_ids)

        if not all_assignee_ids:
            raise BadRequestException("Cần chọn người nhận hoặc team")

        homework_data = data.model_dump(
            exclude={"assignee_ids", "team_ids", "file_url"}
        )

        homework = HomeworkEntity(**homework_data, file_url=file_url)
        homework = self.homework_repo.create(homework)

        for owner_id in all_assignee_ids:
            submission = HomeworkSubmissionEntity(
                homework_id=homework.id,
                owner_id=owner_id,
                status=HomeworkStatus.NOT_SUBMITTED,
                is_late=False,
                link="",
            )
            self.submission_repo.create(submission)

        # Publish Event for decoupled notification
        await EventBus.publish(
            HomeworkAssigned(
                homework_id=homework.id, assignee_ids=list(all_assignee_ids)
            )
        )

        return homework

    async def update(
        self, homework_id: int, data: HomeworkUpdate, file: Optional[UploadFile] = None
    ) -> Optional[HomeworkEntity]:
        homework = self.get_by_id(homework_id)
        if not homework:
            return None

        if file:
            homework.file_url = await self._handle_file(file, data.title)

        update_data = data.model_dump(
            exclude_unset=False, exclude={"assignee_ids", "team_ids", "file_url"}
        )
        for key, value in update_data.items():
            if value is not None:
                setattr(homework, key, value)

        homework = self.homework_repo.update(homework)

        if data.assignee_ids is not None or data.team_ids is not None:
            new_assignee_ids = self._collect_assignee_ids(
                data.assignee_ids, data.team_ids
            )

            if new_assignee_ids:
                current_ids = set(
                    self.submission_repo.get_owner_ids_by_homework(homework_id)
                )

                to_add = new_assignee_ids - current_ids
                for owner_id in to_add:
                    submission = HomeworkSubmissionEntity(
                        homework_id=homework_id,
                        owner_id=owner_id,
                        status=HomeworkStatus.NOT_SUBMITTED,
                        is_late=False,
                        link="",
                    )
                    self.submission_repo.create(submission)

                # Publish Event for new assignees
                if to_add:
                    await EventBus.publish(
                        HomeworkAssigned(
                            homework_id=homework_id, assignee_ids=list(to_add)
                        )
                    )

                to_remove = current_ids - new_assignee_ids
                for owner_id in to_remove:
                    self.submission_repo.delete_by_homework_and_owner(
                        homework_id, owner_id
                    )

        return self.homework_repo.get_by_id(homework_id)

    def delete(self, homework_id: int) -> bool:
        submissions = self.submission_repo.get_all_by_homework(homework_id)
        for submission in submissions:
            self.submission_repo.delete(submission.id)
        return self.homework_repo.delete_by_id(homework_id)

    # --- Homework submissions operations

    def get_submission_of_user(
        self, homework_id: int
    ) -> Optional[HomeworkSubmissionEntity]:
        user_id = get_current_user_id()
        return self.submission_repo.get_by_homework_and_user(homework_id, user_id)

    def get_all_submissions_by_homework(
        self, homework_id: int, current_user: "User"
    ) -> List[HomeworkSubmissionEntity]:
        homework_submissions = self.submission_repo.get_all_by_homework(homework_id)

        role_name = current_user.role.name.lower()
        match role_name:
            case RoleType.ADMIN.value:
                return homework_submissions
            case RoleType.LEADER.value:
                # Need to use team info to filter
                team_member_ids = set()
                teams = self.team_repo.get_all_with_members()
                # find teams that current user belongs to
                my_teams = [
                    t
                    for t in teams
                    if any(tm.user_id == current_user.id for tm in t.team_members)
                ]
                for tm in my_teams:
                    for member in tm.team_members:
                        team_member_ids.add(member.user_id)

                filter_submissions = [
                    item
                    for item in homework_submissions
                    if item.owner_id in team_member_ids
                ]
                return filter_submissions
            case RoleType.TEAMMATE.value:
                filter_submissions = [
                    item
                    for item in homework_submissions
                    if item.owner_id == current_user.id
                ]
                return filter_submissions
            case _:
                raise BadRequestException("Không có quyền xem bài nộp")

    async def submit_homework(
        self, homework_id: int, file: UploadFile
    ) -> HomeworkSubmissionEntity:
        file_content = await file.read()
        file_size = len(file_content)

        validation_error = self.minio_service.validate_file(
            file.filename or "", file_size
        )
        if validation_error:
            raise BadRequestException(validation_error)

        existing_submission = self.get_submission_of_user(homework_id)

        homework = self.homework_repo.get_by_id(homework_id)
        if not homework:
            raise BadRequestException("Không tồn tại homework này")

        now_utc7 = get_current_utc7_time()
        is_late = now_utc7 > homework.deadline
        user_id = get_current_user_id()

        if existing_submission and existing_submission.user_name:
            user_name = existing_submission.user_name.replace(" ", "_")
        else:
            user = self.user_repo.get_by_id(user_id)
            user_name = user.name.replace(" ", "_") if user else f"user_{user_id}"

        homework_title = homework.title.replace(" ", "_").replace("/", "_")
        timestamp = now_utc7.strftime("%Y%m%d_%H%M%S")

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
            submission = self.submission_repo.update(existing_submission)
        else:
            submission_entity = HomeworkSubmissionEntity(
                homework_id=homework_id,
                owner_id=user_id,
                link=file_url,
                status=HomeworkStatus.SUBMITTED,
                is_late=is_late,
            )
            submission = self.submission_repo.create(submission_entity)

        # Publish Event for decoupled violation/notification
        await EventBus.publish(
            HomeworkSubmitted(homework_id=homework_id, user_id=user_id, is_late=is_late)
        )

        return submission

    def update_submission_status(
        self,
        submission_id: int,
        status: HomeworkStatus,
        current_user: "User",
    ) -> Optional[HomeworkSubmissionEntity]:
        submission = self.submission_repo.get_by_id(submission_id)
        if not submission:
            raise BadRequestException("Không tồn tại submission này")

        if submission.status == HomeworkStatus.FINISHED:
            raise BadRequestException("Submission đã được đánh dấu 'finish'")

        if submission.status == HomeworkStatus.NOT_SUBMITTED:
            raise BadRequestException("Submission chưa được nộp, không được check")

        match current_user.role.name:
            case RoleType.ADMIN.value:
                pass
            case RoleType.LEADER.value:
                if submission.status == HomeworkStatus.LEADER_CHECKED:
                    raise BadRequestException(
                        "Submission đã được đánh dấu 'leader đã check'"
                    )

                if status != HomeworkStatus.LEADER_CHECKED:
                    raise BadRequestException(
                        "Leader chỉ có thể đánh dấu 'leader đã check'"
                    )

                # Collect team members
                team_member_ids = set()
                teams = self.team_repo.get_all_with_members()
                my_teams = [
                    t
                    for t in teams
                    if any(tm.user_id == current_user.id for tm in t.team_members)
                ]
                for tm in my_teams:
                    for member in tm.team_members:
                        team_member_ids.add(member.user_id)

                if submission.owner_id not in team_member_ids:
                    raise BadRequestException(
                        "Bạn chỉ có thể update submission của thành viên cùng team"
                    )
            case _:
                raise BadRequestException("Bạn không có quyền thực hiện hành động này")

        submission.status = status
        return self.submission_repo.update(submission)

    def get_unsubmitted_by_user(self, user_id: int) -> List[HomeworkEntity]:
        submissions = self.submission_repo.get_all_by_user(user_id)
        unsubmitted_homeworks = []
        for sub in submissions:
            if sub.status == HomeworkStatus.NOT_SUBMITTED:
                hw = getattr(sub, "homework", None)
                if hw:
                    unsubmitted_homeworks.append(hw)
        return unsubmitted_homeworks
