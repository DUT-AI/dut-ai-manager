"""
Homework Application Use Cases — Facade and original behavior implementation.

Provides clean architecture modularization while maintaining 100% backwards-compatible
imports and identical calculation logic for Dishka providers, controllers, and reports.
"""

from datetime import date, datetime
from typing import Any, cast
from loguru import logger
from sqlalchemy.orm import Session
from app.core.database import engine

from app.homework.application.checker_use_cases import CheckOverdueHomeworkUseCase
from app.homework.application.crud_use_cases import (
    CreateHomeworkUseCase,
    DeleteHomeworkUseCase,
    GetHomeworksUseCase,
    UpdateHomeworkUseCase,
)
from app.homework.application.dtos import (
    CategorySubmissionStatus,
    HomeworkCreate,
    HomeworkReportResponse,
    HomeworkResponse,
    HomeworkSubmissionStatusResponse,
    HomeworkUpdate,
    UserSubmissionInfo,
)
from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.application.submission_use_cases import (
    GetHomeworkSubmissionStatusUseCase,
)
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.homework.infrastructure.repository import HomeworkRepository
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.shared.domain.query_support import QuerySupport
from app.shared.domain.value_objects import UserRef
from app.shared.infrastructure.minio_service import MinioService
from app.team.infrastructure.repository import TeamRepository
from app.user.domain.entity import UserEntity
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time


class HomeworkUseCases:
    """Wrapper cho các use cases của module Homework với logic tính toán nguyên bản."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        user_repo: UserRepository,
        team_repo: TeamRepository,
        minio_service: MinioService,
        quiz_api: QuizApiClient,
        permission_repo: PermissionRequestRepository,
    ):
        self.homework_repo = homework_repo
        self.user_repo = user_repo
        self.team_repo = team_repo
        self.minio_service = minio_service
        self.quiz_api = quiz_api
        self.permission_repo = permission_repo

        self.get_homeworks = GetHomeworksUseCase(
            homework_repo, team_repo, minio_service, quiz_api, permission_repo, user_repo
        )
        self.create_homework = CreateHomeworkUseCase(
            homework_repo, team_repo, minio_service
        )
        self.update_homework = UpdateHomeworkUseCase(
            homework_repo, team_repo, minio_service
        )
        self.delete_homework = DeleteHomeworkUseCase(homework_repo)
        self.get_submission_status_uc = GetHomeworkSubmissionStatusUseCase(
            homework_repo, user_repo, quiz_api, permission_repo, team_repo
        )
        self.check_overdue = CheckOverdueHomeworkUseCase(
            homework_repo, permission_repo, quiz_api, user_repo, team_repo
        )

    def _extract_slug(self, homework: HomeworkEntity) -> str | None:
        return QuizSubmissionHelper.extract_slug_from_entity(homework)

    def _get_effective_assigned_user_ids(self, homework: HomeworkEntity) -> set[int]:
        assigned_uids: set[int] = set()
        user_ids = getattr(homework, "assignee_ids", None) or getattr(homework, "assigned_user_ids", None)
        if user_ids:
            assigned_uids.update(user_ids)

        team_ids = getattr(homework, "team_ids", None) or getattr(homework, "assigned_team_ids", None)
        if team_ids and self.team_repo:
            team_user_ids = self.team_repo.get_user_ids_by_teams(team_ids)
            assigned_uids.update(team_user_ids)

        if not assigned_uids and homework.id and hasattr(self.homework_repo, "get_assigned_user_ids"):
            repo_uids = self.homework_repo.get_assigned_user_ids(homework.id)
            if repo_uids:
                assigned_uids.update(repo_uids)

        return assigned_uids

    def get_by_id(self, homework_id: int) -> HomeworkEntity | None:
        return self.get_homeworks.get_by_id(homework_id)

    def get_all(self, **kwargs) -> list[HomeworkEntity]:
        return self.get_homeworks.get_all(**kwargs)

    def get_assigned_to_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[HomeworkEntity]:
        return self.get_homeworks.get_assigned_to_user(user_id, skip=skip, limit=limit)

    def get_query_support(
        self, query_support: QuerySupport, deleted: bool = False
    ) -> list[HomeworkEntity]:
        return self.get_homeworks.get_query_support(query_support, deleted=deleted)

    async def create(
        self, data: HomeworkCreate, attachment: Any = None
    ) -> HomeworkEntity:
        return await self.create_homework.execute(data, attachment)

    async def update(
        self,
        homework_id: int,
        data: HomeworkUpdate,
        attachment: Any = None,
    ) -> HomeworkEntity | None:
        return await self.update_homework.execute(homework_id, data, attachment)

    def delete(self, homework_id: int) -> bool:
        return self.delete_homework.execute(homework_id)

    def restore(self, homework_id: int) -> HomeworkEntity | None:
        return self.homework_repo.restore(homework_id)

    async def get_submission_status(
        self, homework_id: int
    ) -> HomeworkSubmissionStatusResponse | None:
        return await self.get_submission_status_uc.get_submission_status(homework_id)

    async def get_unsubmitted_by_user(self, user_id: int) -> list[HomeworkEntity]:
        """Return homeworks that a specific user has NOT completed."""
        return await self.get_homeworks.get_unsubmitted_for_user(user_id)

    async def get_unsubmitted_report(self) -> list[HomeworkReportResponse]:
        """Return per-user unsubmitted homework count by combining active homeworks, Quiz API, and violation history."""
        now = get_current_utc7_time().replace(tzinfo=None)
        homeworks = self.homework_repo.get_all(limit=1000)
        active_users = self.user_repo.get_active_users()

        hw_assigned_map: dict[int, set[int]] = {}
        for hw in homeworks:
            if hw.id:
                hw_assigned_map[hw.id] = self._get_effective_assigned_user_ids(hw)

        coding_completed_cache: dict[str, set[int]] = {}
        game_completed_cache: dict[str, set[int]] = {}
        for hw in homeworks:
            slug = self._extract_slug(hw)
            if slug:
                hw_type = QuizSubmissionHelper.detect_homework_type(hw.link, hw.slug)
                if hw_type in ("coding", "both") and slug not in coding_completed_cache:
                    c_ids = await QuizSubmissionHelper.get_coding_completed_user_ids(
                        self.quiz_api, slug
                    )
                    coding_completed_cache[slug] = c_ids if c_ids is not None else set()
                if hw_type in ("game", "both") and slug not in game_completed_cache:
                    g_ids = await QuizSubmissionHelper.get_game_completed_user_ids(
                        self.quiz_api, slug
                    )
                    game_completed_cache[slug] = g_ids if g_ids is not None else set()

        user_hw_violations: dict[int, list[str]] = {}
        try:
            from sqlalchemy import select
            from app.violation.infrastructure.model import ViolationModel

            with Session(engine) as session:
                stmt = select(ViolationModel.user_id, ViolationModel.reason).where(
                    ViolationModel.is_deleted == False,  # noqa: E712
                    (ViolationModel.reason.ilike("%bài tập%"))
                    | (ViolationModel.reason.ilike("%homework%")),
                )
                rows = session.execute(stmt).all()
                for uid, reason in rows:
                    if uid not in user_hw_violations:
                        user_hw_violations[uid] = []
                    if reason:
                        user_hw_violations[uid].append(reason.lower())
        except Exception as exc:
            logger.warning(f"Error fetching violations for homework report: {exc}")

        result: list[HomeworkReportResponse] = []
        for user in active_users:
            if user.id is None:
                continue

            unsubmitted_count = 0
            user_reasons = user_hw_violations.get(user.id, [])

            for hw in homeworks:
                if not hw.id:
                    continue
                assigned_uids = hw_assigned_map.get(hw.id, set())
                if user.id not in assigned_uids:
                    continue

                slug = self._extract_slug(hw)

                if slug:
                    hw_type = QuizSubmissionHelper.detect_homework_type(hw.link, hw.slug)
                    if hw_type in ("coding", "both"):
                        is_coding_submitted = user.id in coding_completed_cache.get(slug, set())
                        if not is_coding_submitted:
                            unsubmitted_count += 1
                    if hw_type in ("game", "both"):
                        is_game_submitted = user.id in game_completed_cache.get(slug, set())
                        if not is_game_submitted:
                            unsubmitted_count += 1
                else:
                    if hw.deadline and hw.deadline.replace(tzinfo=None) > now:
                        unsubmitted_count += 1
                    else:
                        hw_title_clean = hw.title.lower().strip()
                        if any(hw_title_clean in r for r in user_reasons):
                            unsubmitted_count += 1

            result.append(
                HomeworkReportResponse(
                    user_id=user.id,
                    owner=UserRef(
                        id=user.id,
                        name=user.name,
                        email=user.email,
                        avatar_url=user.avatar_url,
                    ),
                    unsubmitted_count=unsubmitted_count,
                )
            )

        result.sort(key=lambda r: r.unsubmitted_count, reverse=True)
        return result


__all__ = [
    "QuizSubmissionHelper",
    "GetHomeworksUseCase",
    "CreateHomeworkUseCase",
    "UpdateHomeworkUseCase",
    "DeleteHomeworkUseCase",
    "GetHomeworkSubmissionStatusUseCase",
    "CheckOverdueHomeworkUseCase",
    "HomeworkUseCases",
]
