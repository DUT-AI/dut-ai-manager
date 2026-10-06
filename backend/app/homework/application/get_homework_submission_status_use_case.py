from datetime import datetime
from typing import Any

from app.homework.application.dtos import (
    CategorySubmissionStatus,
    ExerciseSummaryDTO,
    HomeworkSubmissionStatusResponse,
    StudentExerciseStatusDTO,
    StudentHomeworkDetailDTO,
    UserSubmissionInfo,
)
from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.homework.infrastructure.repository import HomeworkRepository
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time


class GetHomeworkSubmissionStatusUseCase:
    """Return submitted/not_submitted separated by Coding and Game, with per-exercise breakdown."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        user_repo: UserRepository,
        quiz_api: QuizApiClient,
        permission_repo: PermissionRequestRepository | None = None,
    ):
        self.homework_repo = homework_repo
        self.user_repo = user_repo
        self.quiz_api = quiz_api
        self.permission_repo = permission_repo

    def get_by_id(self, homework_id: int) -> HomeworkEntity | None:
        return self.homework_repo.get_by_id(homework_id)

    async def execute(
        self, homework_id: int
    ) -> HomeworkSubmissionStatusResponse | None:
        return await self.get_submission_status(homework_id)

    async def get_submission_status(
        self, homework_id: int
    ) -> HomeworkSubmissionStatusResponse | None:
        """Return submitted/not_submitted separated by Coding and Game, with detailed multi-exercise progress."""
        homework = self.get_by_id(homework_id)
        if not homework:
            return None

        now = get_current_utc7_time().replace(tzinfo=None)
        hw_deadline = (
            homework.deadline.replace(tzinfo=None)
            if homework.deadline.tzinfo is not None
            else homework.deadline
        )
        is_past_deadline = now > hw_deadline

        slug = QuizSubmissionHelper.extract_slug_from_entity(homework)

        # 1. Lấy danh sách bài tập con từ Quiz API
        raw_exercises = (
            await QuizSubmissionHelper.get_lesson_exercises(self.quiz_api, slug)
            if slug
            else []
        ) or []

        coding_exercises_summary: list[ExerciseSummaryDTO] = []
        for idx, ex in enumerate(raw_exercises):
            ex_id = str(ex.get("id"))
            ex_title = ex.get("title") or f"Bài tập {idx + 1}"
            coding_exercises_summary.append(
                ExerciseSummaryDTO(
                    exercise_id=ex_id,
                    title=ex_title,
                    order_index=idx + 1,
                )
            )

        # 2. Lấy dữ liệu Quiz completed map (fallback/tổng hợp)
        coding_map = (
            await QuizSubmissionHelper.get_coding_completed_map(self.quiz_api, slug)
            if slug
            else {}
        ) or {}
        game_map = (
            await QuizSubmissionHelper.get_game_completed_map(self.quiz_api, slug)
            if slug
            else {}
        ) or {}

        coding_completed_uids = set(coding_map.keys())
        game_completed_uids = set(game_map.keys())

        assigned_uids = set(homework.assignee_ids or [])

        postpone_requests = (
            self.permission_repo.get_postpone_requests_for_homeworks(
                homework_ids=[homework.id], user_ids=list(assigned_uids)
            )
            if self.permission_repo and homework.id
            else []
        )
        postpone_map = {(r.created_by, r.homework_id): r for r in postpone_requests}

        all_active_users = {
            u.id: u for u in self.user_repo.get_active_users() if u.id is not None
        }

        # 3. Lấy toàn bộ submission lưu trong database Manager
        db_submissions = (
            self.homework_repo.get_submissions_by_homework(homework.id)
            if self.homework_repo and homework.id
            else []
        )
        db_exercise_map: dict[tuple[int, str], Any] = {}
        db_coding_general_map: dict[int, Any] = {}
        db_game_map: dict[int, Any] = {}

        for sub in db_submissions:
            stype = str(sub.submission_type).upper() if sub.submission_type else "CODING"
            if stype == "CODING":
                if sub.exercise_id:
                    key = (sub.user_id, str(sub.exercise_id))
                    if key not in db_exercise_map:
                        db_exercise_map[key] = sub
                if sub.user_id not in db_coding_general_map:
                    db_coding_general_map[sub.user_id] = sub
            elif stype == "GAME":
                if sub.user_id not in db_game_map:
                    db_game_map[sub.user_id] = sub

        # Nếu Quiz không trả về exercises nhưng trong DB có exercise_id -> bổ sung vào summary
        if not coding_exercises_summary and db_exercise_map:
            known_ex_ids = {k[1] for k in db_exercise_map.keys()}
            for idx, ex_id in enumerate(sorted(known_ex_ids)):
                title = f"Bài tập {idx + 1}"
                for sub in db_submissions:
                    if sub.exercise_id == ex_id and sub.exercise_title:
                        title = sub.exercise_title
                        break
                coding_exercises_summary.append(
                    ExerciseSummaryDTO(
                        exercise_id=ex_id,
                        title=title,
                        order_index=idx + 1,
                    )
                )

        coding_submitted: list[UserSubmissionInfo] = []
        coding_not_submitted: list[UserSubmissionInfo] = []
        game_submitted: list[UserSubmissionInfo] = []
        game_not_submitted: list[UserSubmissionInfo] = []
        students_detail: list[StudentHomeworkDetailDTO] = []

        total_req_coding = len(coding_exercises_summary)

        for uid in assigned_uids:
            user = all_active_users.get(uid) or self.user_repo.get_by_id(uid)
            if not user:
                continue

            user_id = user.id or uid

            req = postpone_map.get((uid, homework.id))
            effective_deadline = hw_deadline
            if req and req.start_time:
                req_time = (
                    req.start_time.replace(tzinfo=None)
                    if req.start_time.tzinfo is not None
                    else req.start_time
                )
                if req_time > effective_deadline:
                    effective_deadline = req_time

            # --- 3.1 Chi tiết từng bài tập coding con ---
            student_exercises: list[StudentExerciseStatusDTO] = []
            completed_coding_count = 0
            coding_has_late = False

            if total_req_coding > 0:
                for ex in coding_exercises_summary:
                    sub = db_exercise_map.get((uid, ex.exercise_id))
                    if sub:
                        sub_dt = (
                            sub.submitted_at.replace(tzinfo=None)
                            if sub.submitted_at and sub.submitted_at.tzinfo is not None
                            else sub.submitted_at
                        )
                        is_late = bool(sub_dt and sub_dt > effective_deadline)
                        if is_late:
                            coding_has_late = True
                        if sub.is_passed:
                            completed_coding_count += 1

                        student_exercises.append(
                            StudentExerciseStatusDTO(
                                exercise_id=ex.exercise_id,
                                exercise_title=ex.title,
                                is_submitted=True,
                                is_passed=sub.is_passed,
                                score=sub.score,
                                attempt_number=sub.attempt_number or 1,
                                submitted_at=sub.submitted_at.isoformat() if sub.submitted_at else None,
                                is_late=is_late,
                            )
                        )
                    else:
                        is_late = is_past_deadline and not (
                            req and req.start_time and now <= req.start_time.replace(tzinfo=None)
                        )
                        student_exercises.append(
                            StudentExerciseStatusDTO(
                                exercise_id=ex.exercise_id,
                                exercise_title=ex.title,
                                is_submitted=False,
                                is_passed=False,
                                score=None,
                                attempt_number=0,
                                submitted_at=None,
                                is_late=is_late,
                            )
                        )
            else:
                # Fallback nếu không có cấu trúc bài con
                is_sub = uid in coding_completed_uids or uid in db_coding_general_map
                if is_sub:
                    completed_coding_count = 1

            if total_req_coding > 0:
                if completed_coding_count >= total_req_coding:
                    coding_status_str = "COMPLETED"
                elif completed_coding_count > 0:
                    coding_status_str = "PARTIALLY_SUBMITTED"
                else:
                    coding_status_str = "NOT_SUBMITTED"
            else:
                coding_status_str = "COMPLETED" if completed_coding_count > 0 else "NOT_SUBMITTED"

            # --- 3.2 Coding Status Categories ---
            if coding_status_str == "COMPLETED":
                coding_submitted.append(
                    UserSubmissionInfo(
                        user_id=user_id,
                        name=user.name,
                        avatar_url=user.avatar_url,
                        is_late=coding_has_late,
                        total_coding_required=total_req_coding,
                        total_coding_completed=completed_coding_count,
                        coding_status=coding_status_str,
                        coding_exercises=student_exercises,
                    )
                )
            else:
                coding_not_submitted.append(
                    UserSubmissionInfo(
                        user_id=user_id,
                        name=user.name,
                        avatar_url=user.avatar_url,
                        is_late=is_past_deadline
                        and not (
                            req
                            and req.start_time
                            and now <= req.start_time.replace(tzinfo=None)
                        ),
                        total_coding_required=total_req_coding,
                        total_coding_completed=completed_coding_count,
                        coding_status=coding_status_str,
                        coding_exercises=student_exercises,
                    )
                )

            # --- 3.3 Game Status ---
            game_is_sub = False
            game_is_late = False
            game_submitted_at_str = None
            game_score_val = None

            if uid in game_completed_uids or uid in db_game_map:
                game_is_sub = True
                entry = game_map.get(uid, {})
                db_sub = db_game_map.get(uid)
                sub_at_raw = (
                    entry.get("submitted_at")
                    or entry.get("completed_at")
                    or (db_sub.submitted_at.isoformat() if db_sub and db_sub.submitted_at else None)
                )
                if sub_at_raw:
                    game_submitted_at_str = str(sub_at_raw)
                    try:
                        sub_dt = datetime.fromisoformat(
                            game_submitted_at_str.replace("Z", "+00:00")
                        ).replace(tzinfo=None)
                        if sub_dt > effective_deadline:
                            game_is_late = True
                    except Exception:
                        pass

                game_score_val = entry.get("final_score") or (db_sub.score if db_sub else None)

                game_submitted.append(
                    UserSubmissionInfo(
                        user_id=user_id,
                        name=user.name,
                        avatar_url=user.avatar_url,
                        is_late=game_is_late,
                        submitted_at=game_submitted_at_str,
                    )
                )
            else:
                game_not_submitted.append(
                    UserSubmissionInfo(
                        user_id=user_id,
                        name=user.name,
                        avatar_url=user.avatar_url,
                        is_late=is_past_deadline
                        and not (
                            req
                            and req.start_time
                            and now <= req.start_time.replace(tzinfo=None)
                        ),
                    )
                )

            students_detail.append(
                StudentHomeworkDetailDTO(
                    user_id=user_id,
                    name=user.name,
                    avatar_url=user.avatar_url,
                    total_coding_required=total_req_coding,
                    total_coding_completed=completed_coding_count,
                    coding_status=coding_status_str,
                    coding_is_late=coding_has_late,
                    coding_exercises=student_exercises,
                    game_is_submitted=game_is_sub,
                    game_is_late=game_is_late,
                    game_submitted_at=game_submitted_at_str,
                    game_score=game_score_val,
                )
            )

        # 3.4 Tính toán số liệu hoàn thành cho từng bài tập con
        total_assigned_count = len(assigned_uids)
        for ex in coding_exercises_summary:
            ex.total_assigned = total_assigned_count
            ex.completed_count = sum(
                1
                for s in students_detail
                if any(
                    ce.exercise_id == ex.exercise_id and ce.is_passed
                    for ce in s.coding_exercises
                )
            )
            ex.completion_rate = (
                round((ex.completed_count / total_assigned_count) * 100, 1)
                if total_assigned_count > 0
                else 0.0
            )

        # 4. Top-level fallback
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
                            user_id=user.id or uid,
                            name=user.name,
                            avatar_url=user.avatar_url,
                        )
                    )

        return HomeworkSubmissionStatusResponse(
            coding=CategorySubmissionStatus(
                submitted=coding_submitted, not_submitted=coding_not_submitted
            ),
            game=CategorySubmissionStatus(
                submitted=game_submitted, not_submitted=game_not_submitted
            ),
            coding_exercises=coding_exercises_summary,
            students=students_detail,
            submitted=top_submitted,
            not_submitted=top_not_submitted,
        )

