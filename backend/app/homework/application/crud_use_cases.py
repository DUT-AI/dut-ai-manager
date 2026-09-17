"""
Homework CRUD Use Cases — application layer.

Handles querying, creation, updating, and deletion of Homework entities.
"""

import asyncio
from fastapi import UploadFile, status
from loguru import logger

from app.core.context import get_current_user_id
from app.homework.application.checker_use_cases import CheckOverdueHomeworkUseCase
from app.homework.application.dtos import (
    HomeworkCreate,
    HomeworkReportResponse,
    HomeworkSubmissionStatusResponse,
    HomeworkUpdate,
)
from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.application.submission_use_cases import (
    GetHomeworkSubmissionStatusUseCase,
)
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.homework.infrastructure.repository import HomeworkRepository
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.shared.application.response import BadRequestException
from app.shared.domain.query_support import QuerySupport
from app.shared.domain.value_objects import UserRef
from app.shared.infrastructure.minio_service import MinioService
from app.team.infrastructure.repository import TeamRepository
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time


class GetHomeworksUseCase:
    """Query homeworks with query support & assigned user / submission filtering."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        team_repo: TeamRepository | None = None,
        minio_service: MinioService | None = None,
        quiz_api: QuizApiClient | None = None,
        permission_repo: PermissionRequestRepository | None = None,
        user_repo: UserRepository | None = None,
    ):
        self.homework_repo = homework_repo
        self.team_repo = team_repo
        self.minio_service = minio_service
        self.quiz_api = quiz_api
        self.permission_repo = permission_repo
        self.user_repo = user_repo

    def get_all(
        self, skip: int = 0, limit: int = 100, deleted: bool = False
    ) -> list[HomeworkEntity]:
        return self.homework_repo.get_all(skip=skip, limit=limit, deleted=deleted)

    def get_assigned_to_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[HomeworkEntity]:
        return self.homework_repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, homework_id: int) -> HomeworkEntity | None:
        return self.homework_repo.get_by_id(homework_id)

    def _get_effective_assigned_user_ids(
        self,
        homework: HomeworkEntity,
        team_cache: dict[tuple[int, ...], list[int]] | None = None,
    ) -> set[int]:
        assigned_uids: set[int] = set()
        user_ids = getattr(homework, "assignee_ids", None) or getattr(
            homework, "assigned_user_ids", None
        )
        if user_ids:
            assigned_uids.update(user_ids)

        team_ids = getattr(homework, "team_ids", None) or getattr(
            homework, "assigned_team_ids", None
        )
        if team_ids and self.team_repo:
            if team_cache is not None:
                key = tuple(sorted(team_ids))
                if key not in team_cache:
                    team_cache[key] = self.team_repo.get_user_ids_by_teams(team_ids)
                assigned_uids.update(team_cache[key])
            else:
                team_user_ids = self.team_repo.get_user_ids_by_teams(team_ids)
                assigned_uids.update(team_user_ids)

        if (
            not assigned_uids
            and homework.id
            and hasattr(self.homework_repo, "get_assigned_user_ids")
        ):
            repo_uids = self.homework_repo.get_assigned_user_ids(homework.id)
            if repo_uids:
                assigned_uids.update(repo_uids)

        return assigned_uids

    def get_query_support(
        self, query_support: QuerySupport, deleted: bool = False
    ) -> list[HomeworkEntity]:
        return self.homework_repo.get_all(query_support=query_support, deleted=deleted)

    async def get_unsubmitted_for_user(self, user_id: int) -> list[HomeworkEntity]:
        """Lấy danh sách bài tập chưa nộp của user_id (kiểm tra Quiz API hoặc DB vi phạm)."""
        all_homeworks = self.homework_repo.get_all()
        now = get_current_utc7_time()

        # 1. Pre-filter homeworks assigned to target user_id
        team_cache: dict[tuple[int, ...], list[int]] = {}
        assigned_homeworks: list[HomeworkEntity] = []
        for hw in all_homeworks:
            if not hw.id:
                continue
            assigned_uids = self._get_effective_assigned_user_ids(
                hw, team_cache=team_cache
            )
            if user_id in assigned_uids:
                assigned_homeworks.append(hw)

        if not assigned_homeworks:
            return []

        # 2. Extract unique slugs only for assigned homeworks
        unique_slugs = list(
            set(
                QuizSubmissionHelper.extract_slug_from_entity(hw)
                for hw in assigned_homeworks
                if QuizSubmissionHelper.extract_slug_from_entity(hw)
            )
        )

        coding_completed_cache: dict[str, set[int]] = {}
        game_completed_cache: dict[str, set[int]] = {}

        # 3. Fetch Quiz API status in parallel via asyncio.gather
        if self.quiz_api and unique_slugs:

            async def fetch_coding(slug: str):
                uids = await QuizSubmissionHelper.get_coding_completed_user_ids(
                    self.quiz_api, slug
                )
                if uids is not None:
                    coding_completed_cache[slug] = uids

            async def fetch_game(slug: str):
                uids = await QuizSubmissionHelper.get_game_completed_user_ids(
                    self.quiz_api, slug
                )
                if uids is not None:
                    game_completed_cache[slug] = uids

            tasks = []
            for slug in unique_slugs:
                tasks.append(fetch_coding(slug))
                tasks.append(fetch_game(slug))
            await asyncio.gather(*tasks)

        # 4. Fetch user violation reasons
        user_reasons: list[str] = []
        try:
            from app.core.database import engine
            from sqlalchemy import text
            from sqlalchemy.orm import Session

            with Session(engine) as session:
                stmt = text(
                    "SELECT reason FROM violations WHERE user_id = :uid AND is_deleted = false"
                ).bindparams(uid=user_id)
                rows = session.scalars(stmt).all()
                user_reasons = [r.lower() for r in rows if r]
        except Exception as exc:
            logger.warning(f"Error fetching user violations: {exc}")

        # 5. Determine unsubmitted homeworks
        unsubmitted: list[HomeworkEntity] = []
        for hw in assigned_homeworks:
            slug = QuizSubmissionHelper.extract_slug_from_entity(hw)

            if slug:
                coding_set = coding_completed_cache.get(slug, set())
                game_set = game_completed_cache.get(slug, set())

                if not QuizSubmissionHelper.is_user_submitted(user_id, coding_set, game_set):
                    unsubmitted.append(hw)
            else:
                if hw.deadline and hw.deadline > now:
                    unsubmitted.append(hw)
                else:
                    hw_title_clean = hw.title.lower().strip()
                    if any(hw_title_clean in r for r in user_reasons):
                        unsubmitted.append(hw)

        return unsubmitted


class CreateHomeworkUseCase:
    """Create a new Homework record."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        team_repo: TeamRepository,
        minio_service: MinioService,
    ):
        self.homework_repo = homework_repo
        self.team_repo = team_repo
        self.minio_service = minio_service

    async def execute(
        self, data: HomeworkCreate, attachment: UploadFile | None = None
    ) -> HomeworkEntity:
        attachment_url = None
        if attachment:
            file_content = await attachment.read()
            filename = f"homeworks/{get_current_utc7_time().strftime('%Y%m%d_%H%M%S')}_{attachment.filename}"
            attachment_url = await self.minio_service.upload_file(
                file_data=file_content,
                filename=filename,
                content_type=attachment.content_type or "application/octet-stream",
            )

        homework = HomeworkEntity(
            title=data.title,
            deadline=data.deadline,
            link=data.link,
            slug=data.slug,
            assignee_ids=data.assignee_ids or [],
            team_ids=data.team_ids or [],
        )

        return self.homework_repo.save(homework)


class UpdateHomeworkUseCase:
    """Update an existing Homework record."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        team_repo: TeamRepository,
        minio_service: MinioService,
    ):
        self.homework_repo = homework_repo
        self.team_repo = team_repo
        self.minio_service = minio_service

    async def execute(
        self,
        homework_id: int,
        data: HomeworkUpdate,
        attachment: UploadFile | None = None,
    ) -> HomeworkEntity:
        existing = self.homework_repo.get_by_id(homework_id)
        if not existing:
            raise BadRequestException(
                "Homework not found", status_code=status.HTTP_404_NOT_FOUND
            )

        updated = existing.model_copy(
            update={
                k: v
                for k, v in {
                    "title": data.title,
                    "deadline": data.deadline,
                    "link": data.link,
                    "slug": data.slug,
                    "assignee_ids": data.assignee_ids,
                    "team_ids": data.team_ids,
                }.items()
                if v is not None
            }
        )

        return self.homework_repo.save(updated)


class DeleteHomeworkUseCase:
    """Soft-delete a Homework record."""

    def __init__(self, homework_repo: HomeworkRepository):
        self.homework_repo = homework_repo

    def execute(self, homework_id: int) -> bool:
        existing = self.homework_repo.get_by_id(homework_id)
        if not existing:
            raise BadRequestException(
                "Homework not found", status_code=status.HTTP_404_NOT_FOUND
            )
        return self.homework_repo.delete(homework_id)


class HomeworkUseCases:
    """Wrapper cho các use cases của module Homework (giúp DI/Providers inject dễ dàng)."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        user_repo: UserRepository | None = None,
        team_repo: TeamRepository | None = None,
        minio_service: MinioService | None = None,
        quiz_api: QuizApiClient | None = None,
        permission_repo: PermissionRequestRepository | None = None,
    ):
        self.homework_repo = homework_repo
        self.user_repo = user_repo
        self.team_repo = team_repo
        self.minio_service = minio_service
        self.quiz_api = quiz_api
        self.permission_repo = permission_repo

        self.get_homeworks = GetHomeworksUseCase(
            homework_repo,
            team_repo,
            minio_service,
            quiz_api,
            permission_repo,
            user_repo,
        )
        self.create_homework = (
            CreateHomeworkUseCase(homework_repo, team_repo, minio_service)  # type: ignore
            if team_repo and minio_service
            else None
        )
        self.update_homework = (
            UpdateHomeworkUseCase(homework_repo, team_repo, minio_service)  # type: ignore
            if team_repo and minio_service
            else None
        )
        self.delete_homework = DeleteHomeworkUseCase(homework_repo)
        self.get_submission_status_uc = (
            GetHomeworkSubmissionStatusUseCase(
                homework_repo,
                user_repo,
                quiz_api,
                permission_repo,
                team_repo,  # type: ignore
            )
            if user_repo and quiz_api
            else None
        )
        self.check_overdue = CheckOverdueHomeworkUseCase(
            homework_repo, permission_repo, quiz_api, user_repo
        )

    def get_by_id(self, homework_id: int) -> HomeworkEntity | None:
        return self.get_homeworks.get_by_id(homework_id)

    def get_all(self, **kwargs) -> list[HomeworkEntity]:
        return self.get_homeworks.get_all(**kwargs)

    def get_assigned_to_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[HomeworkEntity]:
        return self.get_homeworks.get_assigned_to_user(user_id, skip=skip, limit=limit)

    async def create(
        self, data: HomeworkCreate, attachment: UploadFile | None = None
    ) -> HomeworkEntity:
        if not self.create_homework:
            raise BadRequestException("CreateHomeworkUseCase not configured")
        return await self.create_homework.execute(data, attachment)

    async def update(
        self,
        homework_id: int,
        data: HomeworkUpdate,
        attachment: UploadFile | None = None,
    ) -> HomeworkEntity | None:
        if not self.update_homework:
            raise BadRequestException("UpdateHomeworkUseCase not configured")
        return await self.update_homework.execute(homework_id, data, attachment)

    def delete(self, homework_id: int) -> bool:
        return self.delete_homework.execute(homework_id)

    def restore(self, homework_id: int) -> HomeworkEntity | None:
        return self.homework_repo.restore(homework_id)

    async def get_submission_status(
        self, homework_id: int
    ) -> HomeworkSubmissionStatusResponse | None:
        if not self.get_submission_status_uc:
            return None
        return await self.get_submission_status_uc.get_submission_status(homework_id)

    async def get_unsubmitted_by_user(self, user_id: int) -> list[HomeworkEntity]:
        return await self.get_homeworks.get_unsubmitted_for_user(user_id)

    async def get_unsubmitted_report(self) -> list[HomeworkReportResponse]:
        if not self.user_repo:
            return []
        active_users = self.user_repo.get_active_users()
        report: list[HomeworkReportResponse] = []
        for u in active_users:
            if not u.id:
                continue
            unsubmitted_list = await self.get_homeworks.get_unsubmitted_for_user(u.id)
            if unsubmitted_list:
                report.append(
                    HomeworkReportResponse(
                        user_id=u.id,
                        owner=UserRef(
                            id=u.id,
                            name=u.name,
                            email=u.email,
                            avatar_url=getattr(u, "avatar_url", None),
                        ),
                        unsubmitted_count=len(unsubmitted_list),
                    )
                )
        return report
