import re
from datetime import UTC, datetime
from enum import StrEnum

from app.homework.domain.value_objects import (
    CodingSubmissionDetails,
    CompletionStatus,
    ExerciseEvaluation,
    GameSubmissionDetails,
    SubmissionEvaluation,
    TimelinessStatus,
)
from app.shared.domain.base_entity import BaseAuditEntity, BaseEntity, BaseGenericEntity
from app.shared.domain.datetime_types import ensure_utc


class SubmissionType(StrEnum):
    CODING = "CODING"
    GAME = "GAME"


class HomeworkExercise(BaseGenericEntity[int]):
    """Official required coding exercise belonging to a Homework."""

    homework_id: int
    exercise_id: str
    title: str
    order_index: int = 0
    is_active: bool = True


class Homework(BaseAuditEntity):
    """Domain model containing assignment details and SSOT completion rules."""

    title: str
    link: str | None = None
    slug: str | None = None
    requires_coding: bool = True
    requires_game: bool = False
    last_synced_at: datetime | None = None

    @staticmethod
    def extract_slug(link: str | None, slug: str | None) -> str | None:
        """Trích xuất slug từ thuộc tính slug hoặc parse từ URL link (SSOT nghiệp vụ domain)."""
        if slug and slug.strip():
            return slug.strip()
        if link and link.strip():
            link_clean = link.strip()
            match = re.search(r"/(?:homeworks|game|lessons)/([^/?#]+)", link_clean)
            if match:
                return match.group(1).strip()
            if link_clean.startswith("http://") or link_clean.startswith("https://"):
                candidate = (
                    link_clean.rstrip("/")
                    .split("/")[-1]
                    .split("?")[0]
                    .split("#")[0]
                    .strip()
                )
                if candidate and len(candidate) > 1 and " " not in candidate:
                    if candidate.lower() in ("game", "homeworks", "coding"):
                        parts = [p for p in link_clean.rstrip("/").split("/") if p]
                        if len(parts) >= 2:
                            return parts[-2].strip()
                    return candidate
        return None

    @property
    def effective_slug(self) -> str | None:
        """Slug hiệu lực của bài tập, trích xuất từ slug hoặc link."""
        return self.extract_slug(self.link, self.slug)

    def evaluate_submissions(
        self,
        submissions: list["HomeworkSubmission"],
        required_exercises: list[HomeworkExercise] | None = None,
        deadline: datetime | None = None,
        reference_time: datetime | None = None,
    ) -> SubmissionEvaluation:
        """
        Aggregate Root SSOT: Đánh giá 2 chiều độc lập (CompletionStatus x TimelinessStatus).
        - KHÔNG loại bỏ bài nộp sau hạn khỏi trạng thái hoàn thành.
        - Chỉ tính các bài tập con có is_active=True trong danh mục chính thức.
        - Mốc xét đúng hạn là thời điểm sớm nhất trong các lượt nộp đạt (is_passed=True).
        """
        has_coding = self.requires_coding
        has_game = self.requires_game
        if not has_coding and not has_game:
            has_coding = True

        now = ensure_utc(reference_time) if reference_time else datetime.now(UTC)
        dl = ensure_utc(deadline) if deadline is not None else None

        active_exercises = sorted(
            [ex for ex in (required_exercises or []) if ex.is_active],
            key=lambda x: (x.order_index, x.exercise_id),
        )

        (
            coding_exercises_eval,
            total_coding_required,
            total_coding_completed,
            coding_status,
            coding_submitted,
            coding_is_late,
            coding_first_completed_at,
        ) = self._evaluate_coding_part(
            has_coding, submissions, active_exercises, dl, now
        )

        (
            game_submitted,
            game_is_late,
            game_first_passed_at,
            game_best_score,
        ) = self._evaluate_game_part(has_game, submissions, dl)

        uncompleted = self._build_uncompleted_items(
            has_coding,
            coding_submitted,
            total_coding_required,
            total_coding_completed,
            has_game,
            game_submitted,
        )

        all_completed = (not has_coding or coding_submitted) and (
            not has_game or game_submitted
        )
        completion_status, timeliness_status, completed_at = (
            self._resolve_overall_status(
                all_completed=all_completed,
                has_coding=has_coding,
                has_game=has_game,
                total_coding_completed=total_coding_completed,
                game_submitted=game_submitted,
                coding_is_late=coding_is_late,
                game_is_late=game_is_late,
                coding_first_completed_at=coding_first_completed_at,
                game_first_passed_at=game_first_passed_at,
                dl=dl,
                now=now,
            )
        )

        return SubmissionEvaluation(
            completion_status=completion_status,
            timeliness_status=timeliness_status,
            is_submitted=completion_status == CompletionStatus.COMPLETED,
            is_completed_on_time=(
                completion_status == CompletionStatus.COMPLETED
                and timeliness_status == TimelinessStatus.ON_TIME
            ),
            is_late=timeliness_status == TimelinessStatus.LATE,
            is_overdue=timeliness_status == TimelinessStatus.OVERDUE,
            completed_at=completed_at,
            coding_submitted=coding_submitted,
            coding_is_late=coding_is_late,
            coding_status=coding_status,
            total_coding_required=total_coding_required,
            total_coding_completed=total_coding_completed,
            coding_exercises=coding_exercises_eval,
            game_submitted=game_submitted,
            game_is_late=game_is_late,
            game_first_passed_at=game_first_passed_at,
            game_best_score=game_best_score,
            uncompleted_items=uncompleted,
        )

    def _evaluate_coding_part(
        self,
        has_coding: bool,
        submissions: list["HomeworkSubmission"],
        active_exercises: list[HomeworkExercise],
        dl: datetime | None,
        now: datetime,
    ) -> tuple[list[ExerciseEvaluation], int, int, str, bool, bool, datetime | None]:
        if not has_coding:
            return [], 0, 0, "COMPLETED", True, False, None

        if not active_exercises:
            passed_coding = [s for s in submissions if s.is_coding and s.is_passed]
            coding_submitted = len(passed_coding) > 0
            first_at = (
                min(ensure_utc(s.submitted_at) for s in passed_coding)
                if passed_coding
                else None
            )
            is_late = (
                first_at > dl
                if (coding_submitted and dl is not None and first_at is not None)
                else False
            )
            return (
                [],
                1,
                1 if coding_submitted else 0,
                "COMPLETED" if coding_submitted else "NOT_SUBMITTED",
                coding_submitted,
                is_late,
                first_at,
            )

        coding_subs_by_ex: dict[str, list[HomeworkSubmission]] = {}
        for sub in submissions:
            if sub.is_coding and sub.exercise_id:
                coding_subs_by_ex.setdefault(str(sub.exercise_id), []).append(sub)

        coding_evals = [
            self._evaluate_single_exercise(ex, coding_subs_by_ex.get(ex.exercise_id, []), dl, now)
            for ex in active_exercises
        ]
        total_req = len(active_exercises)
        total_done = sum(1 for e in coding_evals if e.is_passed)
        coding_status = self.determine_coding_status(total_done, total_req)
        coding_submitted = coding_status == "COMPLETED"

        first_completed_at: datetime | None = None
        coding_is_late = False
        if coding_submitted:
            passed_ts = [e.first_passed_at for e in coding_evals if e.first_passed_at is not None]
            first_completed_at = max(passed_ts) if passed_ts else None
            coding_is_late = any(e.is_late for e in coding_evals)

        return (
            coding_evals,
            total_req,
            total_done,
            coding_status,
            coding_submitted,
            coding_is_late,
            first_completed_at,
        )

    @staticmethod
    def _evaluate_single_exercise(
        ex: HomeworkExercise,
        ex_subs: list["HomeworkSubmission"],
        dl: datetime | None,
        now: datetime,
    ) -> ExerciseEvaluation:
        passed_subs = [s for s in ex_subs if s.is_passed]
        is_ex_passed = len(passed_subs) > 0
        first_passed_at = (
            min(ensure_utc(s.submitted_at) for s in passed_subs)
            if passed_subs
            else None
        )
        latest_submitted_at = (
            max(ensure_utc(s.submitted_at) for s in ex_subs) if ex_subs else None
        )
        scores = [s.score for s in ex_subs if s.score is not None]
        best_score = max(scores) if scores else None

        if is_ex_passed:
            ex_is_late = (
                first_passed_at > dl
                if (dl is not None and first_passed_at is not None)
                else False
            )
        else:
            ex_is_late = dl is not None and now > dl

        return ExerciseEvaluation(
            exercise_id=ex.exercise_id,
            title=ex.title,
            order_index=ex.order_index,
            is_submitted=len(ex_subs) > 0,
            is_passed=is_ex_passed,
            first_passed_at=first_passed_at,
            latest_submitted_at=latest_submitted_at,
            best_score=best_score,
            attempt_count=len(ex_subs),
            is_late=ex_is_late,
        )

    @staticmethod
    def _evaluate_game_part(
        has_game: bool,
        submissions: list["HomeworkSubmission"],
        dl: datetime | None,
    ) -> tuple[bool, bool, datetime | None, float | None]:
        if not has_game:
            return True, False, None, None
        passed_game = [s for s in submissions if s.is_game and s.is_passed]
        if not passed_game:
            return False, False, None, None
        first_at = min(ensure_utc(s.submitted_at) for s in passed_game)
        scores = [s.score for s in passed_game if s.score is not None]
        best_score = max(scores) if scores else None
        is_late = first_at > dl if dl is not None else False
        return True, is_late, first_at, best_score

    @staticmethod
    def _build_uncompleted_items(
        has_coding: bool,
        coding_submitted: bool,
        total_coding_required: int,
        total_coding_completed: int,
        has_game: bool,
        game_submitted: bool,
    ) -> list[str]:
        uncompleted: list[str] = []
        if has_coding and not coding_submitted:
            if total_coding_required > 1 and total_coding_completed > 0:
                uncompleted.append(
                    f"Còn {total_coding_required - total_coding_completed}/{total_coding_required} bài tập Coding"
                )
            else:
                uncompleted.append("Bài tập Coding")
        if has_game and not game_submitted:
            uncompleted.append("Trắc nghiệm Game")
        return uncompleted

    @staticmethod
    def _resolve_overall_status(
        *,
        all_completed: bool,
        has_coding: bool,
        has_game: bool,
        total_coding_completed: int,
        game_submitted: bool,
        coding_is_late: bool,
        game_is_late: bool,
        coding_first_completed_at: datetime | None,
        game_first_passed_at: datetime | None,
        dl: datetime | None,
        now: datetime,
    ) -> tuple[CompletionStatus, TimelinessStatus, datetime | None]:
        if all_completed:
            timestamps = [
                ts
                for ts in (
                    coding_first_completed_at if has_coding else None,
                    game_first_passed_at if has_game else None,
                )
                if ts is not None
            ]
            completed_at = max(timestamps) if timestamps else None
            is_any_late = (has_coding and coding_is_late) or (
                has_game and game_is_late
            )
            return (
                CompletionStatus.COMPLETED,
                TimelinessStatus.LATE if is_any_late else TimelinessStatus.ON_TIME,
                completed_at,
            )

        has_any_progress = (has_coding and total_coding_completed > 0) or (
            has_game and game_submitted
        )
        completion_status = (
            CompletionStatus.IN_PROGRESS
            if has_any_progress
            else CompletionStatus.NOT_STARTED
        )
        timeliness_status = (
            TimelinessStatus.OVERDUE
            if (dl is not None and now > dl)
            else TimelinessStatus.UPCOMING
        )
        return completion_status, timeliness_status, None

    @staticmethod
    def determine_coding_status(completed_count: int, total_required: int) -> str:
        """Domain Rule: Quy tắc phân loại trạng thái hoàn thành coding."""
        if total_required <= 0:
            return "COMPLETED" if completed_count > 0 else "NOT_SUBMITTED"
        if completed_count >= total_required:
            return "COMPLETED"
        if completed_count > 0:
            return "PARTIALLY_SUBMITTED"
        return "NOT_SUBMITTED"


class HomeworkAssignee(BaseGenericEntity[int]):
    """Domain model for a user assigned to a homework with their individual deadline."""

    homework_id: int
    user_id: int
    deadline: datetime


class HomeworkSubmission(BaseEntity):
    """Base domain model representing an immutable student homework submission attempt."""

    homework_id: int
    user_id: int
    submission_type: SubmissionType
    submitted_at: datetime
    is_passed: bool = True
    details: CodingSubmissionDetails | GameSubmissionDetails | None = None
    exercise_id: str | None = None
    external_submission_id: str | None = None
    exercise_title: str | None = None
    score: float | None = None
    attempt_number: int = 1

    @property
    def is_coding(self) -> bool:
        return self.submission_type == SubmissionType.CODING

    @property
    def is_game(self) -> bool:
        return self.submission_type == SubmissionType.GAME

    @classmethod
    def create_coding(
        cls,
        homework_id: int,
        user_id: int,
        exercise_id: str,
        submitted_at: datetime,
        exercise_title: str | None = None,
        score: float | None = None,
        attempt_number: int = 1,
        is_passed: bool = True,
        details: CodingSubmissionDetails | dict | None = None,
        external_submission_id: str | None = None,
        id: int | None = None,
    ) -> "CodingHomeworkSubmission":
        """Factory method to create a strict, strongly-typed Coding submission."""
        parsed_details = (
            CodingSubmissionDetails(**details)
            if isinstance(details, dict)
            else details
        )
        resolved_ext_id = external_submission_id or (
            parsed_details.submission_id if parsed_details else None
        )
        return CodingHomeworkSubmission(
            id=id,
            homework_id=homework_id,
            user_id=user_id,
            submission_type=SubmissionType.CODING,
            exercise_id=exercise_id,
            external_submission_id=str(resolved_ext_id) if resolved_ext_id else None,
            exercise_title=exercise_title,
            score=score,
            attempt_number=attempt_number,
            submitted_at=submitted_at,
            is_passed=is_passed,
            details=parsed_details,
        )

    @classmethod
    def create_game(
        cls,
        homework_id: int,
        user_id: int,
        submitted_at: datetime,
        score: float | None = None,
        attempt_number: int = 1,
        is_passed: bool = True,
        details: GameSubmissionDetails | dict | None = None,
        external_submission_id: str | None = None,
        id: int | None = None,
    ) -> "GameHomeworkSubmission":
        """Factory method to create a Game quiz submission."""
        parsed_details = (
            GameSubmissionDetails(**details)
            if isinstance(details, dict)
            else details
        )
        resolved_ext_id = external_submission_id or (
            parsed_details.session_id if parsed_details else None
        )
        return GameHomeworkSubmission(
            id=id,
            homework_id=homework_id,
            user_id=user_id,
            submission_type=SubmissionType.GAME,
            external_submission_id=str(resolved_ext_id) if resolved_ext_id else None,
            score=score,
            attempt_number=attempt_number,
            submitted_at=submitted_at,
            is_passed=is_passed,
            details=parsed_details,
        )


class CodingHomeworkSubmission(HomeworkSubmission):
    """
    Domain model for a specific coding exercise submission.
    `exercise_id` is mandatory (non-null) to guarantee exact exercise tracking.
    """

    submission_type: SubmissionType = SubmissionType.CODING
    exercise_id: str
    exercise_title: str | None = None
    score: float | None = None
    attempt_number: int = 1


class GameHomeworkSubmission(HomeworkSubmission):
    """Domain model for an interactive quiz game session attempt."""

    submission_type: SubmissionType = SubmissionType.GAME
    score: float | None = None
    attempt_number: int = 1
