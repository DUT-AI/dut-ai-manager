from typing import Any

from loguru import logger

from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.domain.entity import Homework, HomeworkSubmission, SubmissionType
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.shared.application.response import BadRequestException
from app.shared.domain.datetime_types import parse_datetime_to_utc


class SyncHomeworkFromQuizUseCase:
    """Đồng bộ thủ công (Pull) tất cả bài nộp Coding & Game từ Quiz API về bảng homework_submissions."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
        quiz_api: QuizApiClient,
    ):
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo
        self.quiz_api = quiz_api

    async def execute(self, homework_id: int) -> dict[str, Any]:
        homework = self.homework_repo.get_by_id(homework_id)
        if not homework or not homework.id:
            raise BadRequestException("Không tìm thấy bài tập để đồng bộ")

        slug = QuizSubmissionHelper.extract_slug_from_entity(homework)
        if not slug:
            raise BadRequestException(
                "Bài tập không có đường dẫn/slug hợp lệ để đồng bộ từ Quiz"
            )

        # 0. Làm mới cấu hình và danh mục bài tập con từ Quiz API (Fail-Safe)
        (
            coding_exercises_count,
            game_questions_count,
        ) = await self._refresh_quiz_metadata(homework, slug)

        synced_coding = 0
        updated_coding = 0
        synced_game = 0
        updated_game = 0

        # 1. Đồng bộ Coding nếu bài tập có yêu cầu coding
        if homework.requires_coding:
            synced_coding, updated_coding = await self._sync_coding_submissions(
                homework.id, slug
            )

        # 2. Đồng bộ Game nếu bài tập có yêu cầu game
        if homework.requires_game:
            synced_game, updated_game = await self._sync_game_submissions(
                homework.id, slug
            )

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

        return {
            "homework_id": homework.id,
            "title": homework.title,
            "requires_coding": homework.requires_coding,
            "requires_game": homework.requires_game,
            "coding_exercises_count": coding_exercises_count,
            "game_questions_count": game_questions_count,
            "synced_coding_count": synced_coding,
            "updated_coding_count": updated_coding,
            "synced_game_count": synced_game,
            "updated_game_count": updated_game,
            "message": message,
        }

    async def _refresh_quiz_metadata(
        self, homework: Homework, slug: str
    ) -> tuple[int, int]:
        """Truy vấn metadata và danh mục bài tập con từ Quiz, tự động cập nhật cờ cấu hình bài tập."""
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

        try:
            exercises = await self.quiz_api.get_lesson_exercises(slug)
            if exercises and len(exercises) > coding_count:
                coding_count = len(exercises)
        except Exception as exc:
            logger.warning(
                f"[SyncFromQuiz] Không thể lấy danh sách bài tập con từ Quiz cho slug='{slug}' (ID={homework.id}): {exc}"
            )

        if metadata:
            has_coding = bool(metadata.get("has_coding", False))
            has_game = bool(metadata.get("has_game", False))
            flags_changed = False
            if has_coding != homework.requires_coding:
                homework.requires_coding = has_coding
                flags_changed = True
            if has_game != homework.requires_game:
                homework.requires_game = has_game
                flags_changed = True

            if flags_changed:
                self.homework_repo.save(homework)
                logger.info(
                    f"🔄 [SyncFromQuiz] Đã cập nhật cờ bài tập id={homework.id}: "
                    f"requires_coding={homework.requires_coding}, requires_game={homework.requires_game}"
                )

        return coding_count, game_count

    async def _sync_coding_submissions(
        self, homework_id: int, slug: str
    ) -> tuple[int, int]:
        """Kéo toàn bộ bài nộp Coding từ Quiz API về bảng homework_submissions."""
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

                    details = {
                        "submission_id": sub_id,
                        "exercise_id": str(exercise_id) if exercise_id else None,
                        "exercise_title": exercise_title,
                        "attempt_number": attempt_number,
                        "original_filename": sub.get("original_filename"),
                        "score": score,
                        "status": sub.get("status"),
                        "score_details": sub.get("score_details"),
                        "source": "manual_sync",
                    }

                    existing = self.homework_submission_repo.find_submission_match(
                        homework_id,
                        uid,
                        SubmissionType.CODING,
                        exercise_id=str(exercise_id) if exercise_id else None,
                        quiz_submission_id=sub_id,
                        submitted_at=sub_time,
                    )
                    if existing:
                        self.homework_submission_repo.update_submission(
                            existing,
                            submitted_at=sub_time,
                            is_passed=True,
                            exercise_id=str(exercise_id) if exercise_id else None,
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
                            else f"sync-{homework_id}-{sub_id or uid}"
                        )
                        self.homework_submission_repo.add_submission(
                            HomeworkSubmission.create_coding(
                                homework_id=homework_id,
                                user_id=uid,
                                exercise_id=final_exercise_id,
                                exercise_title=exercise_title,
                                score=score,
                                attempt_number=attempt_number,
                                submitted_at=sub_time,
                                is_passed=True,
                                details=details,
                            )
                        )
                        synced += 1
            else:
                synced_legacy = await self._sync_coding_legacy(homework_id, slug)
                synced += synced_legacy
        except Exception as e:
            logger.warning(f"Error syncing coding submissions for slug={slug}: {e}")

        return synced, updated

    async def _sync_coding_legacy(self, homework_id: int, slug: str) -> int:
        """Fallback sang completed-members nếu submissions-for-sync không khả dụng."""
        synced = 0
        coding_map = await QuizSubmissionHelper.get_coding_completed_map(
            self.quiz_api, slug
        )
        if not coding_map:
            return 0

        for uid, entry in coding_map.items():
            if uid >= 1_000_000:
                continue

            raw_sub_at = entry.get("submitted_at") or entry.get("completed_at")
            sub_time = parse_datetime_to_utc(raw_sub_at)
            if not sub_time:
                continue

            existing = self.homework_submission_repo.find_submission_match(
                homework_id,
                uid,
                SubmissionType.CODING,
                submitted_at=sub_time,
            )
            if not existing:
                self.homework_submission_repo.add_submission(
                    HomeworkSubmission.create_coding(
                        homework_id=homework_id,
                        user_id=uid,
                        exercise_id=f"sync-legacy-{homework_id}-{uid}",
                        submitted_at=sub_time,
                        is_passed=True,
                        details={
                            "max_score": entry.get("max_score"),
                            "submission_count": entry.get("submission_count", 1),
                            "source": "manual_sync",
                        },
                    )
                )
                synced += 1
        return synced

    async def _sync_game_submissions(
        self, homework_id: int, slug: str
    ) -> tuple[int, int]:
        """Kéo toàn bộ bài nộp Game từ Quiz API về bảng homework_submissions."""
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
                    game_score = s.get("final_score")
                    if game_score is not None:
                        game_score = float(game_score)
                    details = {
                        "session_id": session_id,
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
                        quiz_submission_id=session_id,
                        submitted_at=sub_time,
                    )
                    if existing:
                        self.homework_submission_repo.update_submission(
                            existing,
                            submitted_at=sub_time,
                            score=game_score if game_score is not None else existing.score,
                            is_passed=True,
                            details=details,
                        )
                        updated += 1
                    else:
                        self.homework_submission_repo.add_submission(
                            HomeworkSubmission.create_game(
                                homework_id=homework_id,
                                user_id=uid,
                                submitted_at=sub_time,
                                score=game_score,
                                is_passed=True,
                                details=details,
                            )
                        )
                        synced += 1
            else:
                synced_legacy = await self._sync_game_legacy(homework_id, slug)
                synced += synced_legacy
        except Exception as e:
            logger.warning(f"Error syncing game sessions for slug={slug}: {e}")

        return synced, updated

    async def _sync_game_legacy(self, homework_id: int, slug: str) -> int:
        """Fallback sang leaderboard nếu sessions-for-sync không khả dụng."""
        synced = 0
        leaderboard = await self.quiz_api.get_game_leaderboard(slug)
        if not leaderboard:
            return 0

        for row in leaderboard:
            uid = row.get("user_id")
            if not uid or uid >= 1_000_000:
                continue

            is_completed = row.get("is_completed", False)
            total_q = row.get("total_questions", 0)
            ans_q = row.get("answered_questions", 0)

            if is_completed and total_q > 0 and ans_q >= total_q:
                raw_sub_at = row.get("completed_at") or row.get("submitted_at")
                sub_time = parse_datetime_to_utc(raw_sub_at)
                if not sub_time:
                    continue

                existing = self.homework_submission_repo.find_submission_match(
                    homework_id,
                    uid,
                    SubmissionType.GAME,
                    submitted_at=sub_time,
                )
                if not existing:
                    self.homework_submission_repo.add_submission(
                        HomeworkSubmission.create_game(
                            homework_id=homework_id,
                            user_id=uid,
                            submitted_at=sub_time,
                            is_passed=True,
                            details={
                                "final_score": row.get("final_score", 0),
                                "gold": row.get("gold", 0),
                                "attempt_count": row.get("attempt_count", 1),
                                "source": "manual_sync",
                            },
                        )
                    )
                    synced += 1
        return synced
