import asyncio
from datetime import date, datetime
from typing import TYPE_CHECKING, cast

from fastapi import UploadFile
from loguru import logger
from sqlalchemy.orm import Session

from app.core.context import get_current_user_id
from app.core.database import engine
from app.homework.application.dtos import (
    CategorySubmissionStatus,
    HomeworkCreate,
    HomeworkUpdate,
    HomeworkReportResponse,
    HomeworkSubmissionStatusResponse,
    UserSubmissionInfo,
)
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.domain.value_objects import HomeworkOverdueDetected, HomeworkStatus
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
        permission_repo: "PermissionRequestRepository | None" = None,
    ):
        self.homework_repo = homework_repo
        self.user_repo = user_repo
        self.team_repo = team_repo
        self.minio_service = minio_service
        self.quiz_api = quiz_api
        self.permission_repo = permission_repo

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

    async def _get_coding_completed_user_ids(self, slug: str) -> set[int] | None:
        completed_map = await self._get_coding_completed_map(slug)
        if completed_map is None:
            return None
        return set(completed_map.keys())

    async def _get_game_completed_user_ids(self, slug: str) -> set[int] | None:
        completed_map = await self._get_game_completed_map(slug)
        if completed_map is None:
            return None
        return set(completed_map.keys())

    async def _get_coding_completed_map(self, slug: str) -> dict[int, dict] | None:
        if not self.quiz_api:
            return {}
        try:
            members = await self.quiz_api.get_homework_completed_members(slug)
            if members is None:
                return None
            res: dict[int, dict] = {}
            for entry in members:
                if isinstance(entry, dict):
                    uid = entry.get("user_id")
                    if uid is not None and entry.get("submission_count", 1) > 0:
                        res[int(uid)] = entry
                elif isinstance(entry, (int, str)):
                    res[int(entry)] = {"user_id": int(entry)}
            return res
        except Exception as exc:
            logger.warning(f"Quiz completed-members error for slug={slug}: {exc}")
            return {}

    async def _get_game_completed_map(self, slug: str) -> dict[int, dict] | None:
        if not self.quiz_api:
            return {}
        try:
            leaderboard = await self.quiz_api.get_game_leaderboard(slug)
            if leaderboard is None:
                return None
            res: dict[int, dict] = {}
            for entry in leaderboard:
                if isinstance(entry, dict):
                    is_completed = entry.get("is_completed", True)
                    total_q = entry.get("total_questions")
                    ans_q = entry.get("answered_questions")
                    if total_q is not None and ans_q is not None and ans_q < total_q:
                        is_completed = False
                    uid = entry.get("user_id")
                    if is_completed and uid:
                        res[int(uid)] = entry
                elif isinstance(entry, (int, str)):
                    res[int(entry)] = {"user_id": int(entry)}
            return res
        except Exception as exc:
            logger.warning(f"Quiz leaderboard error for slug={slug}: {exc}")
            return {}

    def _get_effective_assigned_user_ids(self, homework: HomeworkEntity) -> set[int]:
        """
        Lấy danh sách user_id được phân công cho bài tập.
        Nếu bài tập không được gán cho ai (assignee_ids và team_ids đều rỗng),
        fallback về tất cả active users để tương thích với dữ liệu cũ.
        """
        assigned_uids = self.homework_repo.get_assigned_user_ids(homework.id) if homework.id else set()
        if not assigned_uids:
            active_users = self.user_repo.get_active_users()
            assigned_uids = {
                u.id for u in active_users
                if u.id is not None
            }
        return assigned_uids

    async def create(
        self, data: HomeworkCreate
    ) -> HomeworkEntity:
        
        homework_data = data.model_dump(
            exclude={"assignee_ids", "team_ids"}
        )

        extracted_slug = self._extract_slug_from_str(data.link, data.slug)
        if extracted_slug:
            homework_data["slug"] = extracted_slug

        team_ids = data.team_ids or []
        assignee_uids = set(data.assignee_ids or [])
        if team_ids:
            team_user_ids = self.team_repo.get_user_ids_by_teams(team_ids)
            assignee_uids.update(team_user_ids)

        homework = HomeworkEntity(
            **homework_data,
            assignee_ids=list(assignee_uids),
            team_ids=team_ids,
        )
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

        team_ids = data.team_ids if data.team_ids is not None else homework.team_ids
        assignee_uids = set(data.assignee_ids if data.assignee_ids is not None else homework.assignee_ids)
        if data.team_ids is not None and data.team_ids:
            team_user_ids = self.team_repo.get_user_ids_by_teams(data.team_ids)
            assignee_uids.update(team_user_ids)

        if data.assignee_ids is not None or data.team_ids is not None:
            homework.assignee_ids = list(assignee_uids)
        if data.team_ids is not None:
            homework.team_ids = data.team_ids

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

        hw_assigned_map: dict[int, set[int]] = {}
        for hw in homeworks:
            if hw.id:
                hw_assigned_map[hw.id] = self._get_effective_assigned_user_ids(hw)

        # Cache completed members per slug to avoid repeated requests
        coding_completed_cache: dict[str, set[int]] = {}
        game_completed_cache: dict[str, set[int]] = {}
        for hw in homeworks:
            slug = self._extract_slug(hw)
            if slug:
                if slug not in coding_completed_cache:
                    c_ids = await self._get_coding_completed_user_ids(slug)
                    coding_completed_cache[slug] = c_ids if c_ids is not None else set()
                if slug not in game_completed_cache:
                    g_ids = await self._get_game_completed_user_ids(slug)
                    game_completed_cache[slug] = g_ids if g_ids is not None else set()

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
                if not hw.id:
                    continue
                assigned_uids = hw_assigned_map.get(hw.id, set())
                if user.id not in assigned_uids:
                    continue

                slug = self._extract_slug(hw)

                if slug:
                    is_coding_submitted = user.id in coding_completed_cache.get(slug, set())
                    is_game_submitted = user.id in game_completed_cache.get(slug, set())
                    
                    if not is_coding_submitted:
                        unsubmitted_count += 1
                    if not is_game_submitted:
                        unsubmitted_count += 1
                else:
                    if hw.deadline and hw.deadline > now:
                        # Ongoing/upcoming homework: user has not completed yet
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

    async def get_unsubmitted_by_user(self, user_id: int) -> list[HomeworkEntity]:
        """Return homeworks that a specific user has NOT completed."""
        now = get_current_utc7_time().replace(tzinfo=None)
        homeworks = self.homework_repo.get_all(limit=1000)

        coding_completed_cache: dict[str, set[int]] = {}
        game_completed_cache: dict[str, set[int]] = {}
        for hw in homeworks:
            slug = self._extract_slug(hw)
            if slug:
                if slug not in coding_completed_cache:
                    c_ids = await self._get_coding_completed_user_ids(slug)
                    coding_completed_cache[slug] = c_ids if c_ids is not None else set()
                if slug not in game_completed_cache:
                    g_ids = await self._get_game_completed_user_ids(slug)
                    game_completed_cache[slug] = g_ids if g_ids is not None else set()

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
            if not hw.id:
                continue
            assigned_uids = self._get_effective_assigned_user_ids(hw)
            if user_id not in assigned_uids:
                continue

            slug = self._extract_slug(hw)

            if slug:
                is_coding_submitted = user_id in coding_completed_cache.get(slug, set())
                is_game_submitted = user_id in game_completed_cache.get(slug, set())
                
                # If they missed either, append the homework
                if not is_coding_submitted or not is_game_submitted:
                    unsubmitted.append(hw)
            else:
                if hw.deadline and hw.deadline > now:
                    unsubmitted.append(hw)
                else:
                    hw_title_clean = hw.title.lower().strip()
                    if any(hw_title_clean in r for r in user_reasons):
                        unsubmitted.append(hw)

        return unsubmitted

    async def get_submission_status(self, homework_id: int) -> HomeworkSubmissionStatusResponse | None:
        """Return submitted/not_submitted separated by Coding and Game, with late detection."""
        homework = self.get_by_id(homework_id)
        if not homework:
            return None

        now = get_current_utc7_time().replace(tzinfo=None)
        hw_deadline = homework.deadline.replace(tzinfo=None) if homework.deadline.tzinfo is not None else homework.deadline
        is_past_deadline = (now > hw_deadline)

        slug = self._extract_slug(homework)

        coding_map = await self._get_coding_completed_map(slug) if slug else {}
        game_map = await self._get_game_completed_map(slug) if slug else {}

        coding_completed_uids = set(coding_map.keys()) if coding_map is not None else set()
        game_completed_uids = set(game_map.keys()) if game_map is not None else set()

        assigned_uids = self._get_effective_assigned_user_ids(homework)

        postpone_requests = (
            self.permission_repo.get_postpone_requests_for_homeworks(
                homework_ids=[homework.id], user_ids=list(assigned_uids)
            ) if self.permission_repo else []
        )
        postpone_map = {(r.created_by, r.homework_id): r for r in postpone_requests}

        all_active_users = {u.id: u for u in self.user_repo.get_active_users() if u.id is not None}

        coding_submitted: list[UserSubmissionInfo] = []
        coding_not_submitted: list[UserSubmissionInfo] = []
        game_submitted: list[UserSubmissionInfo] = []
        game_not_submitted: list[UserSubmissionInfo] = []

        for uid in assigned_uids:
            user = all_active_users.get(uid)
            if not user:
                user = self.user_repo.get_by_id(uid)
            if not user:
                continue

            req = postpone_map.get((uid, homework.id))
            effective_deadline = hw_deadline
            if req and req.start_time:
                req_time = req.start_time.replace(tzinfo=None) if req.start_time.tzinfo is not None else req.start_time
                if req_time > effective_deadline:
                    effective_deadline = req_time

            # --- Coding Status ---
            if uid in coding_completed_uids:
                entry = coding_map.get(uid, {})
                submitted_at_str = entry.get("submitted_at") or entry.get("completed_at")
                is_late = False
                if submitted_at_str:
                    try:
                        sub_dt = datetime.fromisoformat(str(submitted_at_str).replace("Z", "+00:00")).replace(tzinfo=None)
                        if sub_dt > effective_deadline:
                            is_late = True
                    except Exception:
                        if now > effective_deadline:
                            is_late = True
                else:
                    if now > effective_deadline:
                        is_late = True

                coding_submitted.append(
                    UserSubmissionInfo(
                        user_id=user.id,
                        name=user.name,
                        avatar_url=user.avatar_url,
                        is_late=is_late,
                        submitted_at=str(submitted_at_str) if submitted_at_str else None,
                    )
                )
            else:
                coding_not_submitted.append(
                    UserSubmissionInfo(
                        user_id=user.id,
                        name=user.name,
                        avatar_url=user.avatar_url,
                        is_late=is_past_deadline and not (req and req.start_time and now <= req.start_time.replace(tzinfo=None)),
                    )
                )

            # --- Game Status ---
            if uid in game_completed_uids:
                entry = game_map.get(uid, {})
                submitted_at_str = entry.get("submitted_at") or entry.get("completed_at")
                is_late = False
                if submitted_at_str:
                    try:
                        sub_dt = datetime.fromisoformat(str(submitted_at_str).replace("Z", "+00:00")).replace(tzinfo=None)
                        if sub_dt > effective_deadline:
                            is_late = True
                    except Exception:
                        if now > effective_deadline:
                            is_late = True
                else:
                    if now > effective_deadline:
                        is_late = True

                game_submitted.append(
                    UserSubmissionInfo(
                        user_id=user.id,
                        name=user.name,
                        avatar_url=user.avatar_url,
                        is_late=is_late,
                        submitted_at=str(submitted_at_str) if submitted_at_str else None,
                    )
                )
            else:
                game_not_submitted.append(
                    UserSubmissionInfo(
                        user_id=user.id,
                        name=user.name,
                        avatar_url=user.avatar_url,
                        is_late=is_past_deadline and not (req and req.start_time and now <= req.start_time.replace(tzinfo=None)),
                    )
                )

        # Combined top-level fallback
        combined_submitted_ids = set()
        top_submitted: list[UserSubmissionInfo] = []
        top_not_submitted: list[UserSubmissionInfo] = []

        for info in coding_submitted + game_submitted:
            if info.user_id not in combined_submitted_ids:
                combined_submitted_ids.add(info.user_id)
                top_submitted.append(info)

        for uid in assigned_uids:
            if uid not in combined_submitted_ids:
                user = all_active_users.get(uid) or self.user_repo.get_by_id(uid)
                if user:
                    top_not_submitted.append(
                        UserSubmissionInfo(
                            user_id=user.id,
                            name=user.name,
                            avatar_url=user.avatar_url,
                        )
                    )

        return HomeworkSubmissionStatusResponse(
            coding=CategorySubmissionStatus(submitted=coding_submitted, not_submitted=coding_not_submitted),
            game=CategorySubmissionStatus(submitted=game_submitted, not_submitted=game_not_submitted),
            submitted=top_submitted,
            not_submitted=top_not_submitted,
        )

class CheckOverdueHomeworkUseCase:
    """Kiểm tra bài tập quá hạn và tạo vi phạm tự động dựa trên kết quả từ Quiz API."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        permission_repo: PermissionRequestRepository,
        quiz_api: QuizApiClient,
        user_repo: UserRepository,
    ):
        self.homework_repo = homework_repo
        self.permission_repo = permission_repo
        self.quiz_api = quiz_api
        self.user_repo = user_repo

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

    async def _get_coding_completed_user_ids(self, slug: str) -> set[int] | None:
        completed_map = await self._get_coding_completed_map(slug)
        if completed_map is None:
            return None
        return set(completed_map.keys())

    async def _get_game_completed_user_ids(self, slug: str) -> set[int] | None:
        completed_map = await self._get_game_completed_map(slug)
        if completed_map is None:
            return None
        return set(completed_map.keys())

    async def _get_coding_completed_map(self, slug: str) -> dict[int, dict] | None:
        if not self.quiz_api:
            return {}
        try:
            members = await self.quiz_api.get_homework_completed_members(slug)
            if members is None:
                return None
            res: dict[int, dict] = {}
            for entry in members:
                if isinstance(entry, dict):
                    uid = entry.get("user_id")
                    if uid is not None and entry.get("submission_count", 1) > 0:
                        res[int(uid)] = entry
                elif isinstance(entry, (int, str)):
                    res[int(entry)] = {"user_id": int(entry)}
            return res
        except Exception as exc:
            logger.warning(f"Quiz completed-members error for slug={slug}: {exc}")
            return {}

    async def _get_game_completed_map(self, slug: str) -> dict[int, dict] | None:
        if not self.quiz_api:
            return {}
        try:
            leaderboard = await self.quiz_api.get_game_leaderboard(slug)
            if leaderboard is None:
                return None
            res: dict[int, dict] = {}
            for entry in leaderboard:
                if isinstance(entry, dict):
                    is_completed = entry.get("is_completed", True)
                    total_q = entry.get("total_questions")
                    ans_q = entry.get("answered_questions")
                    if total_q is not None and ans_q is not None and ans_q < total_q:
                        is_completed = False
                    uid = entry.get("user_id")
                    if is_completed and uid:
                        res[int(uid)] = entry
                elif isinstance(entry, (int, str)):
                    res[int(entry)] = {"user_id": int(entry)}
            return res
        except Exception as exc:
            logger.warning(f"Quiz leaderboard error for slug={slug}: {exc}")
            return {}

    async def execute(self, target_date: date | None = None) -> int:
        now = get_current_utc7_time().replace(tzinfo=None)
        if target_date is None:
            target_date = now.date()

        homeworks = self.homework_repo.get_by_deadline_date(target_date)
        if not homeworks:
            return 0

        created_count = 0

        for homework in homeworks:
            if not homework.id:
                continue

            # Skip if deadline has not passed yet
            hw_deadline = homework.deadline.replace(tzinfo=None) if homework.deadline.tzinfo is not None else homework.deadline
            if now <= hw_deadline:
                continue

            slug = (homework.slug or "").strip()

            completed_coding_user_ids: set[int] | None = None
            completed_game_user_ids: set[int] | None = None

            if slug:
                completed_coding_user_ids = await self._get_coding_completed_user_ids(slug)
                completed_game_user_ids = await self._get_game_completed_user_ids(slug)

            assigned_uids = self.homework_repo.get_assigned_user_ids(homework.id)
            if not assigned_uids:
                active_users = self.user_repo.get_active_users()
                assigned_uids = {
                    u.id for u in active_users
                    if u.id is not None
                }
            member_user_ids = list(assigned_uids)

            postpone_requests = (
                self.permission_repo.get_postpone_requests_for_homeworks(
                    homework_ids=[homework.id], user_ids=member_user_ids
                )
            )
            # Use created_by instead of user_id for permission request
            postpone_map = {(r.created_by, r.homework_id): r for r in postpone_requests}

            for user_id in member_user_ids:
                req = postpone_map.get((user_id, homework.id))

                if req and req.start_time and now <= req.start_time.replace(tzinfo=None):
                    continue

                is_postponed_expired = bool(req)

                if slug:
                    # Penalty for coding part if it exists
                    if completed_coding_user_ids is not None:
                        if user_id not in completed_coding_user_ids:
                            reason = (
                                f"Chưa hoàn thành bài tập code ({slug}) quá thời gian xin hẹn"
                                if is_postponed_expired
                                else f"Chưa hoàn thành bài tập code ({slug}) và không phép"
                            )
                            await EventBus.publish(
                                HomeworkOverdueDetected(
                                    user_id=user_id,
                                    homework_id=homework.id,
                                    homework_title=homework.title,
                                    deadline_date=str(homework.deadline.date()),
                                    reason=reason,
                                )
                            )
                            created_count += 1
                            
                    # Penalty for game part if it exists
                    if completed_game_user_ids is not None:
                        if user_id not in completed_game_user_ids:
                            reason = (
                                f"Chưa hoàn thành bài tập game ({slug}) quá thời gian xin hẹn"
                                if is_postponed_expired
                                else f"Chưa hoàn thành bài tập game ({slug}) và không phép"
                            )
                            await EventBus.publish(
                                HomeworkOverdueDetected(
                                    user_id=user_id,
                                    homework_id=homework.id,
                                    homework_title=homework.title,
                                    deadline_date=str(homework.deadline.date()),
                                    reason=reason,
                                )
                            )
                            created_count += 1
                else:
                    # Logic without slug could be omitted or implemented differently.
                    pass

        return created_count