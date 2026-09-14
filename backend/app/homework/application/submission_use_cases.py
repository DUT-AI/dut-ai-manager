"""
Homework Submission Use Cases — application layer.

Handles querying submission status breakdown (Coding & Game) with late detection.
"""

from datetime import datetime

from app.homework.application.dtos import (
    CategorySubmissionStatus,
    HomeworkSubmissionStatusResponse,
    UserSubmissionInfo,
)
from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.homework.infrastructure.repository import HomeworkRepository
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.team.infrastructure.repository import TeamRepository
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time


class GetHomeworkSubmissionStatusUseCase:
    """Return submitted/not_submitted separated by Coding and Game, with late detection."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        user_repo: UserRepository,
        quiz_api: QuizApiClient,
        permission_repo: PermissionRequestRepository | None = None,
        team_repo: TeamRepository | None = None,
    ):
        self.homework_repo = homework_repo
        self.user_repo = user_repo
        self.quiz_api = quiz_api
        self.permission_repo = permission_repo
        self.team_repo = team_repo

    def get_by_id(self, homework_id: int) -> HomeworkEntity | None:
        return self.homework_repo.get_by_id(homework_id)

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

    async def execute(self, homework_id: int) -> HomeworkSubmissionStatusResponse | None:
        return await self.get_submission_status(homework_id)

    async def get_submission_status(self, homework_id: int) -> HomeworkSubmissionStatusResponse | None:
        """Return submitted/not_submitted separated by Coding and Game, with late detection."""
        homework = self.get_by_id(homework_id)
        if not homework:
            return None

        now = get_current_utc7_time().replace(tzinfo=None)
        hw_deadline = homework.deadline.replace(tzinfo=None) if homework.deadline.tzinfo is not None else homework.deadline
        is_past_deadline = (now > hw_deadline)

        slug = QuizSubmissionHelper.extract_slug_from_entity(homework)

        coding_map = await QuizSubmissionHelper.get_coding_completed_map(self.quiz_api, slug) if slug else {}
        game_map = await QuizSubmissionHelper.get_game_completed_map(self.quiz_api, slug) if slug else {}

        coding_completed_uids = set(coding_map.keys()) if coding_map is not None else set()
        game_completed_uids = set(game_map.keys()) if game_map is not None else set()

        assigned_uids = self._get_effective_assigned_user_ids(homework)

        postpone_requests = (
            self.permission_repo.get_postpone_requests_for_homeworks(
                homework_ids=[homework.id], user_ids=list(assigned_uids)
            ) if self.permission_repo and homework.id else []
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
                submitted_at_str = (
                    entry.get("submitted_at")
                    or entry.get("completed_at")
                    or entry.get("updated_at")
                    or entry.get("created_at")
                )
                is_late = False
                if submitted_at_str:
                    try:
                        sub_dt = datetime.fromisoformat(
                            str(submitted_at_str).replace("Z", "+00:00")
                        ).replace(tzinfo=None)
                        if sub_dt > effective_deadline:
                            is_late = True
                    except Exception:
                        pass
                elif entry.get("is_late") is True:
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
                submitted_at_str = (
                    entry.get("submitted_at")
                    or entry.get("completed_at")
                    or entry.get("updated_at")
                    or entry.get("created_at")
                )
                is_late = False
                if submitted_at_str:
                    try:
                        sub_dt = datetime.fromisoformat(
                            str(submitted_at_str).replace("Z", "+00:00")
                        ).replace(tzinfo=None)
                        if sub_dt > effective_deadline:
                            is_late = True
                    except Exception:
                        pass
                elif entry.get("is_late") is True:
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
