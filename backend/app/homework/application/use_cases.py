import asyncio
from datetime import date
from typing import TYPE_CHECKING, cast

from fastapi import UploadFile
from loguru import logger
from sqlalchemy.orm import Session

from app.core.context import get_current_user_id
from app.core.database import engine
from app.homework.application.dtos import (
    HomeworkCreate,
    HomeworkUpdate,
    HomeworkReportResponse,
    HomeworkSubmissionStatusResponse,
    UserSubmissionInfo,
)
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.homework.infrastructure.repository import (
    HomeworkRepository,
)
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.rbac.domain.entity import RoleType
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import EventBus
from app.shared.domain.value_objects import UserRef
from app.shared.infrastructure.minio_service import MinioService
from app.team.domain.entity import Team
from app.team.infrastructure.repository import TeamRepository
from app.user.domain.entity import UserEntity
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time


class HomeworkUseCases:
    def __init__(
        self,
        homework_repo: HomeworkRepository,
        user_repo: UserRepository,
        team_repo: TeamRepository,
        minio_service: MinioService,
        quiz_api: "QuizApiClient | None" = None,
    ):
        self.homework_repo = homework_repo
        self.user_repo = user_repo
        self.team_repo = team_repo
        self.minio_service = minio_service
        self.quiz_api = quiz_api

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

    @staticmethod
    def _extract_slug_from_str(link: str | None, slug: str | None) -> str | None:
        if slug and slug.strip():
            return slug.strip()
        if link and link.strip():
            link_clean = link.strip()
            import re
            match = re.search(r"/(?:homeworks|game)/([^/?#]+)", link_clean)
            if match:
                return match.group(1).strip()
            if link_clean.startswith("http://") or link_clean.startswith("https://"):
                candidate = link_clean.rstrip("/").split("/")[-1].split("?")[0].split("#")[0].strip()
                if candidate and len(candidate) > 1 and " " not in candidate:
                    return candidate
        return None

    def _extract_slug(self, homework: HomeworkEntity) -> str | None:
        return self._extract_slug_from_str(homework.link, homework.slug)

    async def _get_completed_user_ids_for_slug(self, slug: str) -> set[int]:
        if not self.quiz_api:
            return set()

        completed_uids: set[int] = set()

        # 1. Check coding homework completed members
        try:
            members = await self.quiz_api.get_homework_completed_members(slug)
            for entry in members:
                if isinstance(entry, dict):
                    uid = entry.get("user_id")
                    if uid is not None and entry.get("submission_count", 1) > 0:
                        completed_uids.add(int(uid))
                elif isinstance(entry, (int, str)):
                    completed_uids.add(int(entry))
        except Exception as exc:
            logger.warning(f"Quiz completed-members error for slug={slug}: {exc}")

        # 2. Check game quiz leaderboard
        try:
            leaderboard = await self.quiz_api.get_game_leaderboard(slug)
            for entry in leaderboard:
                if isinstance(entry, dict):
                    is_completed = entry.get("is_completed", True)
                    total_q = entry.get("total_questions")
                    ans_q = entry.get("answered_questions")
                    if total_q is not None and ans_q is not None and ans_q < total_q:
                        is_completed = False
                    if is_completed and entry.get("user_id"):
                        completed_uids.add(int(entry["user_id"]))
                elif isinstance(entry, (int, str)):
                    completed_uids.add(int(entry))
        except Exception as exc:
            logger.warning(f"Quiz leaderboard error for slug={slug}: {exc}")

        return completed_uids

    async def create(
        self, data: HomeworkCreate
    ) -> HomeworkEntity:
        
        homework_data = data.model_dump(
            exclude={"assignee_ids", "team_ids"}
        )

        extracted_slug = self._extract_slug_from_str(data.link, data.slug)
        if extracted_slug:
            homework_data["slug"] = extracted_slug

        homework = HomeworkEntity(**homework_data)
        homework = self.homework_repo.create(homework)
        assert homework.id is not None
        
        return homework

    async def update(
        self, homework_id: int, data: HomeworkUpdate
    ) -> HomeworkEntity | None:
        homework = self.get_by_id(homework_id)
        if not homework:
            return None

        update_data = data.model_dump(
            exclude_unset=False, exclude={"assignee_ids", "team_ids"}
        )

        extracted_slug = self._extract_slug_from_str(
            update_data.get("link") or homework.link,
            update_data.get("slug") or homework.slug,
        )
        if extracted_slug:
            update_data["slug"] = extracted_slug

        for key, value in update_data.items():
            if value is not None:
                setattr(homework, key, value)

        homework = self.homework_repo.update(homework)
        
        return self.homework_repo.get_by_id(homework_id)

    def delete(self, homework_id: int) -> bool:
        assert homework_id is not None
        return self.homework_repo.delete_by_id(homework_id)

    def restore(self, homework_id: int) -> HomeworkEntity | None:
        return self.homework_repo.restore(homework_id)

    async def get_unsubmitted_report(self) -> list[HomeworkReportResponse]:
        """Return per-user unsubmitted homework count by combining active homeworks, Quiz API, and violation history."""
        now = get_current_utc7_time().replace(tzinfo=None)
        homeworks = self.homework_repo.get_all(limit=1000)
        active_users = self.user_repo.get_active_users()

        # Cache completed members per slug to avoid repeated requests
        slug_completed_cache: dict[str, set[int]] = {}
        for hw in homeworks:
            slug = self._extract_slug(hw)
            if slug and slug not in slug_completed_cache:
                slug_completed_cache[slug] = await self._get_completed_user_ids_for_slug(slug)

        # Pre-fetch historical homework violations: user_id -> list of lowercased reasons
        user_hw_violations: dict[int, list[str]] = {}
        try:
            from sqlalchemy import select
            from app.violation.infrastructure.model import ViolationModel
            with Session(engine) as session:
                stmt = select(ViolationModel.user_id, ViolationModel.reason).where(
                    ViolationModel.is_deleted == False,
                    (ViolationModel.reason.ilike("%bài tập%")) | (ViolationModel.reason.ilike("%homework%"))
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
                slug = self._extract_slug(hw)
                is_submitted = False

                if slug and slug in slug_completed_cache:
                    completed_uids = slug_completed_cache[slug]
                    if user.id in completed_uids:
                        is_submitted = True

                if not is_submitted:
                    if hw.deadline and hw.deadline > now:
                        # Ongoing/upcoming homework: user has not completed yet
                        unsubmitted_count += 1
                    else:
                        # Past deadline homework:
                        if slug:
                            unsubmitted_count += 1
                        else:
                            # Check if user has a violation recorded for this homework
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

    async def get_unsubmitted_by_user(self, user_id: int) -> list[HomeworkEntity]:
        """Return homeworks that a specific user has NOT completed."""
        now = get_current_utc7_time().replace(tzinfo=None)
        homeworks = self.homework_repo.get_all(limit=1000)

        slug_completed_cache: dict[str, set[int]] = {}
        for hw in homeworks:
            slug = self._extract_slug(hw)
            if slug and slug not in slug_completed_cache:
                slug_completed_cache[slug] = await self._get_completed_user_ids_for_slug(slug)

        user_reasons: list[str] = []
        try:
            from sqlalchemy import select
            from app.violation.infrastructure.model import ViolationModel
            with Session(engine) as session:
                stmt = select(ViolationModel.reason).where(
                    ViolationModel.user_id == user_id,
                    ViolationModel.is_deleted == False,
                    (ViolationModel.reason.ilike("%bài tập%")) | (ViolationModel.reason.ilike("%homework%"))
                )
                rows = session.scalars(stmt).all()
                user_reasons = [r.lower() for r in rows if r]
        except Exception as exc:
            logger.warning(f"Error fetching user violations: {exc}")

        unsubmitted: list[HomeworkEntity] = []
        for hw in homeworks:
            slug = self._extract_slug(hw)
            is_submitted = False

            if slug and slug in slug_completed_cache:
                completed_uids = slug_completed_cache[slug]
                if user_id in completed_uids:
                    is_submitted = True

            if not is_submitted:
                if hw.deadline and hw.deadline > now:
                    unsubmitted.append(hw)
                else:
                    if slug:
                        unsubmitted.append(hw)
                    else:
                        hw_title_clean = hw.title.lower().strip()
                        if any(hw_title_clean in r for r in user_reasons):
                            unsubmitted.append(hw)

        return unsubmitted

    async def get_submission_status(self, homework_id: int) -> HomeworkSubmissionStatusResponse | None:
        """Return submitted/not_submitted based on HW coding API only."""
        homework = self.get_by_id(homework_id)
        if not homework:
            return None

        slug = self._extract_slug(homework)
        active_users = self.user_repo.get_active_users()

        completed_uids: set[int] = set()
        if slug and self.quiz_api:
            try:
                members = await self.quiz_api.get_homework_completed_members(slug)
                for entry in members:
                    if isinstance(entry, dict):
                        uid = entry.get("user_id")
                        if uid is not None and entry.get("submission_count", 1) > 0:
                            completed_uids.add(int(uid))
                    elif isinstance(entry, (int, str)):
                        completed_uids.add(int(entry))
            except Exception as exc:
                logger.warning(f"Quiz hw completed-members error for slug={slug}: {exc}")

        # Exclude admin – they don't need to submit homework
        NON_MEMBER_ROLES = "admin"
        member_users = [
            u for u in active_users
            if u.id is not None
            and not any(r.lower() in NON_MEMBER_ROLES for r in u.role_names)
        ]

        submitted: list[UserSubmissionInfo] = []
        not_submitted: list[UserSubmissionInfo] = []

        for user in member_users:

            info = UserSubmissionInfo(
                user_id=user.id,
                name=user.name,
                avatar_url=user.avatar_url,
            )
            if user.id in completed_uids:
                submitted.append(info)
            else:
                not_submitted.append(info)

        return HomeworkSubmissionStatusResponse(
            submitted=submitted,
            not_submitted=not_submitted,
        )
