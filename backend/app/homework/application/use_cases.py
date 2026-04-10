import asyncio
import httpx
from datetime import date
from sqlmodel import Session
from app.core.database import engine
from app.core.config import settings
from loguru import logger
from typing import List, Optional, Set
from app.core.context import get_current_user_id
from app.homework.application.dtos import HomeworkCreate, HomeworkUpdate
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.domain.entity import HomeworkSubmission as HomeworkSubmissionEntity
from app.homework.domain.value_objects import (
    HomeworkAssigned,
    HomeworkStatus,
    HomeworkSubmitted,
    HomeworkGraded,
)
from app.homework.infrastructure.repository import (
    HomeworkRepository,
    HomeworkSubmissionRepository,
)
from app.rbac.domain.entity import RoleType
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import EventBus
from app.shared.infrastructure.minio_service import MinioService
from app.team.domain.entity import Team
from app.team.infrastructure.repository import TeamRepository
from app.user.domain.entity import UserEntity
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time
from fastapi import UploadFile


from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.homework.infrastructure.model import HomeworkSubmissionModel
from app.homework.domain.value_objects import HomeworkOverdueDetected


from app.homework.infrastructure.external_api import HomeworkGradingService


class CheckOverdueHomeworkUseCase:
    """Kiểm tra bài tập quá hạn và tạo vi phạm tự động"""

    def __init__(
        self,
        submission_repo: HomeworkSubmissionRepository,
        permission_repo: PermissionRequestRepository,
    ):
        self.submission_repo = submission_repo
        self.permission_repo = permission_repo

    async def execute(self, target_date: Optional[date] = None):
        """
        Logic:
        1. Lấy tất cả các bài nộp chưa nộp có deadline là hôm nay.
        2. Với mỗi bài nộp:
           - Kiểm tra xem user có đơn xin hoãn (POSTPONE) cho bài tập (homework_id) không.
           - Nếu có đơn hoãn, kiểm tra xem hiện tại đã quá hạn của đơn chưa (`start_time`). Nếu quá hạn -> vi phạm.
           - Nếu KHÔNG có đơn hoãn, kiểm tra xem hiện tại đã quá hạn deadline của bài tập chưa -> vi phạm.
        """
        now = get_current_utc7_time().replace(tzinfo=None)
        if target_date is None:
            target_date = now.date()

        overdue_submissions = self.submission_repo.get_not_submitted_for_deadline_date(
            target_date
        )

        if not overdue_submissions:
            return 0

        # Tối ưu N+1: Lấy toàn bộ đơn xin hoãn theo user_id + homework_id
        owner_ids = list({sub.owner_id for sub in overdue_submissions})
        homework_ids = list(
            {sub.homework_id for sub in overdue_submissions if sub.homework_id}
        )

        postpone_requests = self.permission_repo.get_postpone_requests_for_homeworks(
            homework_ids=homework_ids, user_ids=owner_ids
        )
        postpone_map = {(r.user_id, r.homework_id): r for r in postpone_requests}

        created_count = 0
        for sub in overdue_submissions:
            user_id = sub.owner_id
            homework = sub.homework

            if not homework:
                continue

            # Kiểm tra xem hiện tại đã quá deadline gốc chưa
            if now <= homework.deadline:
                continue

            req = postpone_map.get((user_id, homework.id))

            if req:
                if req.start_time and now <= req.start_time:
                    continue

                reason = "Không nộp bài tập quá thời gian xin hẹn"
            else:
                reason = "Không nộp bài tập và không phép"

            # Phát sự kiện phát hiện quá hạn bài tập
            await EventBus.publish(
                HomeworkOverdueDetected(
                    user_id=user_id,
                    homework_id=homework.id or 0,
                    homework_title=homework.title,
                    deadline_date=str(homework.deadline.date()),
                    reason=reason,
                )
            )
            created_count += 1

        return created_count


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
        assert file.filename is not None
        content = await file.read()
        error = self.minio_service.validate_file(file.filename, len(content))
        if error:
            raise BadRequestException(error)

        now_utc7 = get_current_utc7_time()
        timestamp = now_utc7.strftime("%y%m%d_%H%M%S")
        filename = f"{self.minio_service.HOMEWORK_PREFIX}/{title}/{file.filename.split('.')[0]}_{timestamp}"

        file_url = self.minio_service.upload_file(
            content, filename, file.content_type or "application/octet-stream"
        )
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
        assert homework.id is not None

        submissions_to_create = [
            HomeworkSubmissionEntity(
                homework_id=homework.id,
                owner_id=owner_id,
                status=HomeworkStatus.NOT_SUBMITTED,
                is_late=False,
                link="",
            )
            for owner_id in all_assignee_ids
        ]
        if submissions_to_create:
            self.submission_repo.bulk_create(submissions_to_create)

        # Publish Event for decoupled notification
        await EventBus.publish(
            HomeworkAssigned(
                homework_id=homework.id, assignee_ids=list(all_assignee_ids)
            )
        )

        # Fire-and-forget: notify external homework service
        asyncio.create_task(homework.notify_external_homework_api())

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
                to_add_submissions = [
                    HomeworkSubmissionEntity(
                        homework_id=homework_id,
                        owner_id=owner_id,
                        status=HomeworkStatus.NOT_SUBMITTED,
                        is_late=False,
                        link="",
                    )
                    for owner_id in to_add
                ]
                if to_add_submissions:
                    self.submission_repo.bulk_create(to_add_submissions)

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
        assert homework_id is not None
        submissions = self.submission_repo.get_all_by_homework(homework_id)
        for submission in submissions:
            assert submission.id is not None
            self.submission_repo.delete(submission.id)
        return self.homework_repo.delete_by_id(homework_id)

    # --- Homework submissions operations

    def get_submission_of_user(
        self, homework_id: int
    ) -> Optional[HomeworkSubmissionEntity]:
        user_id = get_current_user_id()
        assert user_id is not None
        return self.submission_repo.get_by_homework_and_user(homework_id, user_id)

    def get_all_submissions_by_homework(
        self, homework_id: int, current_user: UserEntity
    ) -> List[HomeworkSubmissionEntity]:
        homework_submissions = self.submission_repo.get_all_by_homework(homework_id)

        role_name = current_user.role_name or ""
        role_name = role_name.lower()
        match role_name:
            case RoleType.ADMIN.value:
                return homework_submissions
            case RoleType.LEADER.value:
                # Need to use team info to filter
                team_member_ids = set()
                teams: List[Team] = self.team_repo.get_all_with_members()
                # find teams that current user belongs to
                my_teams = [
                    t
                    for t in teams
                    if any(tm.user_id == current_user.id for tm in t.members)
                ]
                for tm in my_teams:
                    for member in tm.members:
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

        now_utc7 = get_current_utc7_time().replace(tzinfo=None)
        is_late = now_utc7 > homework.deadline
        user_id = get_current_user_id()
        assert user_id is not None

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

        assert submission is not None
        # Publish Event for decoupled violation/notification
        await EventBus.publish(
            HomeworkSubmitted(homework_id=homework_id, user_id=user_id, is_late=is_late)
        )

        assert submission.id is not None
        # Push assignment to external API for grading
        asyncio.create_task(
            self.create_and_save_submission_feedback(
                submission_id=submission.id,
                file_url=file_url,
                homework_id=homework_id,
                user_id=user_id,
            )
        )

        return submission

    def update_submission_status(
        self,
        submission_id: int,
        status: HomeworkStatus,
        current_user: UserEntity,
    ) -> Optional[HomeworkSubmissionEntity]:
        submission = self.submission_repo.get_by_id(submission_id)
        if not submission:
            raise BadRequestException("Không tồn tại submission này")

        if submission.status == HomeworkStatus.FINISHED:
            raise BadRequestException("Submission đã được đánh dấu 'finish'")

        if submission.status == HomeworkStatus.NOT_SUBMITTED:
            raise BadRequestException("Submission chưa được nộp, không được check")

        assert current_user.role_name is not None
        match current_user.role_name:
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
                    if any(tm.user_id == current_user.id for tm in t.members)
                ]
                for tm in my_teams:
                    for member in tm.members:
                        team_member_ids.add(member.user_id)

                if submission.owner_id not in team_member_ids:
                    raise BadRequestException(
                        "Bạn chỉ có thể update submission của thành viên cùng team"
                    )
            case _:
                raise BadRequestException("Bạn không có quyền thực hiện hành động này")

        submission.status = status
        return self.submission_repo.update(submission)

    async def create_and_save_submission_feedback(
        self, submission_id: int, file_url: str, homework_id: int, user_id: int
    ) -> None:
        """Gọi API external để chấm bài, và cập nhật lại DB của submission đó khi xong."""
        try:
            logger.info(f"Đang gọi API external chấm bài cho code: {submission_id}")

            # 1. Gọi external service (Infrastructure Layer)
            data = await HomeworkGradingService.fetch_grading(
                file_url, homework_id, user_id
            )
            logger.info(f"Dữ liệu trả về từ API external: {data}")

            is_pass = data.get("is_pass", False)
            score = data.get("score")
            feedback = data.get("feedback") or "Không có feedback"
            score_details = data.get("score_details", []) or []
            plagiarism_info = data.get("plagiarism", []) or []

            # 2. Xử lý lưu kết quả với Transaction (Application Layer)
            with Session(engine) as session:
                repo = HomeworkSubmissionRepository(session)
                submission_entity = repo.get_by_id(submission_id)
                if submission_entity:
                    # 3. Apply Domain Logic (Domain Layer)
                    submission_entity.update_grading_result(
                        is_pass=is_pass,
                        score=score,
                        feedback=feedback,
                        score_details=score_details,
                        plagiarism_info=plagiarism_info,
                    )

                    # 4. Lưu lại thông qua Repository (Infrastructure / Application)
                    repo.update(submission_entity)
                    session.commit()
                    
                    is_plagiarized = submission_entity.is_plagiarized

            # 5. Phát sự kiện sau khi đã lưu xong
            await EventBus.publish(
                HomeworkGraded(
                    homework_id=homework_id,
                    user_id=user_id,
                    score=score,
                    is_pass=is_pass,
                    is_plagiarized=is_plagiarized
                )
            )

            logger.info(
                f"Cập nhật thành công điểm cho bài {submission_id} (Đạo văn: {is_plagiarized})"
            )

        except Exception as e:
            logger.exception(
                f"Lỗi khi đánh giá bài chấm (submission_id={submission_id}): {str(e)}"
            )

    def get_unsubmitted_by_user(self, user_id: int) -> List[HomeworkEntity]:
        submissions = self.submission_repo.get_all_by_user(user_id)
        unsubmitted_homeworks = []
        for sub in submissions:
            if sub.status == HomeworkStatus.NOT_SUBMITTED:
                hw = getattr(sub, "homework", None)
                if hw:
                    unsubmitted_homeworks.append(hw)
        return unsubmitted_homeworks

    def get_unsubmitted_report(self) -> List[dict]:
        counts = self.submission_repo.get_unsubmitted_counts_per_user()
        # get all active users
        users = self.user_repo.get_all()
        report = []
        for u in users:
            if not u.is_active:
                continue
            report.append(
                {
                    "user_id": u.id,
                    "user_name": u.name,
                    "user_avatar": u.avatar_url,
                    "unsubmitted_count": counts.get(u.id, 0),
                }
            )

        report.sort(key=lambda x: x["unsubmitted_count"], reverse=True)
        return report
