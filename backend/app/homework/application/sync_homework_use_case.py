from datetime import UTC, datetime
from typing import Any

from loguru import logger

from app.homework.application.dtos import SyncHomeworkResult
from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.domain.entity import (
    Homework,
    HomeworkExercise,
    HomeworkSubmission,
    SubmissionType,
)
from app.homework.domain.ports import (
    HomeworkExerciseRepositoryPort,
    HomeworkRepositoryPort,
    HomeworkSubmissionRepositoryPort,
)
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.shared.application.response import BadRequestException
from app.shared.domain.datetime_types import parse_datetime_to_utc

FAILED_CODING_STATUSES = frozenset(
    {
        "FAILED",
        "FAIL",
        "ERROR",
        "REJECTED",
        "WRONG_ANSWER",
        "TIME_LIMIT_EXCEEDED",
        "MEMORY_LIMIT_EXCEEDED",
        "COMPILE_ERROR",
        "RUNTIME_ERROR",
        "INCOMPLETE",
        "PENDING",
    }
)


class SyncHomeworkFromQuizUseCase:
    """
    Đồng bộ (Pull) danh mục bài tập con chính thức và toàn bộ lượt nộp Coding & Game
    từ Quiz API về hệ thống theo chế độ append-only idempotent.
    """

    def __init__(
        self,
        homework_repo: HomeworkRepositoryPort,
        homework_submission_repo: HomeworkSubmissionRepositoryPort,
        homework_exercise_repo: HomeworkExerciseRepositoryPort,
        quiz_api: QuizApiClient,
    ):
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo
        self.homework_exercise_repo = homework_exercise_repo
        self.quiz_api = quiz_api

    async def execute(
        self, homework_id: int, sync_submissions: bool = True
    ) -> SyncHomeworkResult:
        homework = self.homework_repo.get_by_id(homework_id)
        if not homework or not homework.id:
            raise BadRequestException("Không tìm thấy bài tập để đồng bộ")

        slug = QuizSubmissionHelper.extract_slug_from_entity(homework)
        if not slug:
            raise BadRequestException(
                "Bài tập không có đường dẫn/slug hợp lệ để đồng bộ từ Quiz"
            )

        # 0. Làm mới cấu hình và danh mục bài tập con chính thức từ Quiz API (Fail-Safe)
        (
            coding_exercises_count,
            game_questions_count,
        ) = await self._refresh_quiz_metadata_and_exercises(homework, slug)

        synced_coding = 0
        updated_coding = 0
        synced_game = 0
        updated_game = 0

        if sync_submissions:
            if homework.requires_coding:
                synced_coding, updated_coding = await self._sync_coding_submissions(
                    homework.id, slug
                )
            if homework.requires_game:
                synced_game, updated_game = await self._sync_game_submissions(
                    homework.id, slug
                )

        synced_at = datetime.now(UTC)
        homework.last_synced_at = synced_at
        self.homework_repo.save(homework)

        logger.info(
            f"✅ [SyncFromQuiz] Hoàn tất đồng bộ bài tập id={homework_id}: "
            f"Requires Coding={homework.requires_coding} ({coding_exercises_count} bài tập con), "
            f"Requires Game={homework.requires_game} ({game_questions_count} câu hỏi) | "
            f"Coding: +{synced_coding} mới, ~{updated_coding} cập nhật | "
            f"Game: +{synced_game} mới, ~{updated_game} cập nhật"
        )

        parts = []
        if homework.requires_coding:
            parts.append(f"{coding_exercises_count} bài tập coding")
        if homework.requires_game:
            parts.append(f"{game_questions_count} câu hỏi game")
        summary_scope = " & ".join(parts) if parts else "không yêu cầu coding/game"

        message = (
            f"Đồng bộ thành công: Nhận diện {summary_scope}. "
            f"Coding (+{synced_coding} mới, ~{updated_coding} cập nhật), "
            f"Game (+{synced_game} mới, ~{updated_game} cập nhật)."
        )

        return SyncHomeworkResult(
            homework_id=homework.id,
            title=homework.title,
            requires_coding=homework.requires_coding,
            requires_game=homework.requires_game,
            coding_exercises_count=coding_exercises_count,
            game_questions_count=game_questions_count,
            synced_coding_count=synced_coding,
            updated_coding_count=updated_coding,
            synced_game_count=synced_game,
            updated_game_count=updated_game,
            last_synced_at=synced_at,
            message=message,
        )

    @staticmethod
    def _resolve_coding_is_passed(sub: dict[str, Any]) -> bool:
        """Tôn trọng trạng thái đạt/không đạt thực tế từ Quiz API thay vì ép cứng True."""
        if sub.get("is_passed") is not None:
            return bool(sub["is_passed"])
        raw_status = sub.get("status")
        if raw_status is not None:
            normalized = str(raw_status).strip().upper()
            if normalized in FAILED_CODING_STATUSES:
                return False
        return True

    async def _refresh_quiz_metadata_and_exercises(
        self, homework: Homework, slug: str
    ) -> tuple[int, int]:
        """Truy vấn metadata & danh mục bài con từ Quiz, cập nhật homework_exercises (Fail-Safe)."""
        assert homework.id is not None
        coding_count = 0
        game_count = 0
        metadata = None

        try:
            metadata = await self.quiz_api.get_lesson_metadata(slug)
            if metadata:
                coding_count = int(metadata.get("coding_count") or 0)
                game_count = int(metadata.get("game_question_count") or 0)
        except Exception as exc:
            logger.warning(
                f"[SyncFromQuiz] Không thể lấy metadata từ Quiz cho slug='{slug}' (ID={homework.id}): {exc}"
            )

        if metadata:
            has_coding = bool(metadata.get("has_coding", False))
            has_game = bool(metadata.get("has_game", False))
            if has_coding != homework.requires_coding or has_game != homework.requires_game:
                homework.requires_coding = has_coding
                homework.requires_game = has_game
                self.homework_repo.save(homework)
                logger.info(
                    f"🔄 [SyncFromQuiz] Đã cập nhật cờ bài tập id={homework.id}: "
                    f"requires_coding={homework.requires_coding}, requires_game={homework.requires_game}"
                )

        # Đồng bộ bảng homework_exercises chính thức (chỉ cập nhật khi Quiz API trả danh sách hợp lệ)
        try:
            exercises = await self.quiz_api.get_lesson_exercises(slug)
            if exercises is not None:
                entities = [
                    HomeworkExercise(
                        homework_id=homework.id,
                        exercise_id=str(ex["id"]),
                        title=str(ex.get("title") or f"Bài tập {idx + 1}"),
                        order_index=idx + 1,
                        is_active=True,
                    )
                    for idx, ex in enumerate(exercises)
                    if isinstance(ex, dict) and ex.get("id")
                ]
                synced_entities = self.homework_exercise_repo.sync_exercises(
                    homework.id, entities
                )
                coding_count = len(synced_entities)
            else:
                existing_active = self.homework_exercise_repo.get_active_by_homework(
                    homework.id
                )
                if existing_active:
                    coding_count = len(existing_active)
        except Exception as exc:
            logger.warning(
                f"[SyncFromQuiz] Không thể lấy danh sách bài tập con từ Quiz cho slug='{slug}' (ID={homework.id}): {exc}"
            )
            existing_active = self.homework_exercise_repo.get_active_by_homework(
                homework.id
            )
            if existing_active:
                coding_count = len(existing_active)

        return coding_count, game_count

    async def _sync_coding_submissions(
        self, homework_id: int, slug: str
    ) -> tuple[int, int]:
        """Kéo toàn bộ bài nộp Coding từ Quiz API về bảng homework_submissions (Append-Only Idempotent)."""
        synced = 0
        updated = 0
        try:
            submissions = await self.quiz_api.get_homework_submissions_for_sync(slug)
            if submissions is not None:
                for sub in submissions:
                    uid = sub.get("user_id")
                    if not uid or uid >= 1_000_000:
                        continue

                    raw_sub_at = sub.get("submitted_at")
                    sub_time = parse_datetime_to_utc(raw_sub_at)
                    if not sub_time:
                        logger.warning(
                            f"[SyncFromQuiz] Bỏ qua bài nộp Coding user_id={uid} (slug='{slug}') "
                            f"do Quiz không có timestamp hợp lệ: {sub}"
                        )
                        continue

                    sub_id = sub.get("submission_id")
                    ext_id = str(sub_id).strip() if sub_id is not None and str(sub_id).strip() else None
                    exercise_id = sub.get("exercise_id") or sub.get("homework_id")
                    exercise_title = sub.get("exercise_title")
                    score = (
                        float(sub["score"]) if sub.get("score") is not None else None
                    )
                    attempt_number = (
                        int(sub.get("attempt_number", 1))
                        if sub.get("attempt_number") is not None
                        else 1
                    )
                    is_passed = self._resolve_coding_is_passed(sub)

                    details = {
                        "submission_id": ext_id,
                        "original_filename": sub.get("original_filename"),
                        "status": sub.get("status"),
                        "score_details": sub.get("score_details"),
                        "source": "manual_sync",
                    }

                    existing = self.homework_submission_repo.find_submission_match(
                        homework_id,
                        uid,
                        SubmissionType.CODING,
                        exercise_id=str(exercise_id) if exercise_id else None,
                        external_submission_id=ext_id,
                        submitted_at=sub_time,
                    )
                    if existing:
                        self.homework_submission_repo.update_submission(
                            existing,
                            submitted_at=sub_time,
                            is_passed=is_passed,
                            exercise_id=str(exercise_id) if exercise_id else None,
                            external_submission_id=ext_id,
                            exercise_title=exercise_title,
                            score=score,
                            attempt_number=attempt_number,
                            details=details,
                        )
                        updated += 1
                    else:
                        final_exercise_id = (
                            str(exercise_id)
                            if exercise_id
                            else f"sync-{homework_id}-{ext_id or uid}"
                        )
                        self.homework_submission_repo.add_submission(
                            HomeworkSubmission.create_coding(
                                homework_id=homework_id,
                                user_id=uid,
                                exercise_id=final_exercise_id,
                                external_submission_id=ext_id,
                                exercise_title=exercise_title,
                                score=score,
                                attempt_number=attempt_number,
                                submitted_at=sub_time,
                                is_passed=is_passed,
                                details=details,
                            )
                        )
                        synced += 1
        except Exception as e:
            logger.warning(f"Error syncing coding submissions for slug={slug}: {e}")

        return synced, updated

    async def _sync_game_submissions(
        self, homework_id: int, slug: str
    ) -> tuple[int, int]:
        """Kéo toàn bộ bài nộp Game từ Quiz API về bảng homework_submissions (Append-Only Idempotent)."""
        synced = 0
        updated = 0
        try:
            game_sessions = await self.quiz_api.get_game_sessions_for_sync(slug)
            if game_sessions is not None:
                for s in game_sessions:
                    uid = s.get("user_id")
                    if not uid or uid >= 1_000_000:
                        continue

                    if not s.get("is_completed", False):
                        continue

                    raw_sub_at = s.get("completed_at")
                    sub_time = parse_datetime_to_utc(raw_sub_at)
                    if not sub_time:
                        logger.warning(
                            f"[SyncFromQuiz] Bỏ qua Game session user_id={uid} (slug='{slug}') "
                            f"do Quiz không có completed_at hợp lệ: {s}"
                        )
                        continue

                    session_id = s.get("session_id")
                    ext_id = (
                        str(session_id).strip()
                        if session_id is not None and str(session_id).strip()
                        else None
                    )
                    game_score = s.get("final_score")
                    if game_score is not None:
                        game_score = float(game_score)
                    details = {
                        "session_id": ext_id,
                        "final_score": game_score,
                        "gold": s.get("gold", 0),
                        "attempt_count": s.get("attempt_count", 1),
                        "total_questions": s.get("total_questions", 0),
                        "correct_count": s.get("correct_count", 0),
                        "source": "manual_sync",
                    }

                    existing = self.homework_submission_repo.find_submission_match(
                        homework_id,
                        uid,
                        SubmissionType.GAME,
                        external_submission_id=ext_id,
                        submitted_at=sub_time,
                    )
                    if existing:
                        self.homework_submission_repo.update_submission(
                            existing,
                            submitted_at=sub_time,
                            score=game_score if game_score is not None else existing.score,
                            is_passed=True,
                            external_submission_id=ext_id,
                            details=details,
                        )
                        updated += 1
                    else:
                        self.homework_submission_repo.add_submission(
                            HomeworkSubmission.create_game(
                                homework_id=homework_id,
                                user_id=uid,
                                external_submission_id=ext_id,
                                submitted_at=sub_time,
                                score=game_score,
                                is_passed=True,
                                details=details,
                            )
                        )
                        synced += 1
        except Exception as e:
            logger.warning(f"Error syncing game sessions for slug={slug}: {e}")

        return synced, updated
