from typing import Any

from loguru import logger

from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.domain.entity import HomeworkSubmission, SubmissionType
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.homework.infrastructure.repository import HomeworkRepository
from app.shared.application.response import BadRequestException
from app.utils.datetime import get_current_utc7_time, to_utc7_naive


class SyncHomeworkFromQuizUseCase:
    """Đồng bộ thủ công (Pull) tất cả bài nộp Coding & Game từ Quiz API về bảng homework_submissions."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        quiz_api: QuizApiClient,
    ):
        self.homework_repo = homework_repo
        self.quiz_api = quiz_api

    async def execute(self, homework_id: int) -> dict[str, Any]:
        homework = self.homework_repo.get_by_id(homework_id)
        if not homework or not homework.id:
            raise BadRequestException("Không tìm thấy bài tập để đồng bộ")

        slug = QuizSubmissionHelper.extract_slug_from_entity(homework)
        if not slug:
            raise BadRequestException("Bài tập không có đường dẫn/slug hợp lệ để đồng bộ từ Quiz")

        now = get_current_utc7_time()
        synced_coding = 0
        updated_coding = 0
        synced_game = 0
        updated_game = 0

        # 1. Đồng bộ Coding nếu bài tập có yêu cầu coding
        if homework.requires_coding:
            try:
                # 1.1 Thử lấy danh sách đầy đủ tất cả các lần nộp (Full History)
                submissions = await self.quiz_api.get_homework_submissions_for_sync(slug)
                if submissions is not None:
                    for sub in submissions:
                        uid = sub.get("user_id")
                        if not uid or uid >= 1_000_000:
                            continue

                        raw_sub_at = sub.get("submitted_at")
                        sub_time = to_utc7_naive(raw_sub_at)
                        if not sub_time:
                            logger.warning(
                                f"[SyncFromQuiz] Bỏ qua bài nộp Coding user_id={uid} (slug='{slug}') "
                                f"do Quiz không có timestamp hợp lệ: {sub}"
                            )
                            continue

                        sub_id = sub.get("submission_id")
                        details = {
                            "submission_id": sub_id,
                            "attempt_number": sub.get("attempt_number"),
                            "original_filename": sub.get("original_filename"),
                            "score": sub.get("score"),
                            "status": sub.get("status"),
                            "score_details": sub.get("score_details"),
                            "source": "manual_sync",
                        }

                        # Đối soát xem bài nộp này đã có trong Manage chưa
                        existing = self.homework_repo.find_submission_match(
                            homework.id,
                            uid,
                            SubmissionType.CODING,
                            quiz_submission_id=sub_id,
                            submitted_at=sub_time,
                        )
                        if existing:
                            # Ghi đè / Cập nhật lại thông tin mới nhất
                            self.homework_repo.update_submission(
                                existing,
                                submitted_at=sub_time,
                                is_passed=True,
                                details=details,
                            )
                            updated_coding += 1
                        else:
                            # Thêm mới vào lịch sử nộp bài
                            self.homework_repo.add_submission(
                                HomeworkSubmission(
                                    homework_id=homework.id,
                                    user_id=uid,
                                    submission_type=SubmissionType.CODING,
                                    submitted_at=sub_time,
                                    is_passed=True,
                                    details=details,
                                )
                            )
                            synced_coding += 1
                else:
                    # 1.2 Fallback sang completed-members nếu submissions-for-sync không khả dụng
                    coding_map = await QuizSubmissionHelper.get_coding_completed_map(
                        self.quiz_api, slug
                    )
                    if coding_map:
                        for uid, entry in coding_map.items():
                            if uid >= 1_000_000:
                                continue

                            raw_sub_at = entry.get("submitted_at") or entry.get("completed_at")
                            sub_time = to_utc7_naive(raw_sub_at)
                            if not sub_time:
                                continue

                            existing = self.homework_repo.find_submission_match(
                                homework.id,
                                uid,
                                SubmissionType.CODING,
                                submitted_at=sub_time,
                            )
                            if not existing:
                                self.homework_repo.add_submission(
                                    HomeworkSubmission(
                                        homework_id=homework.id,
                                        user_id=uid,
                                        submission_type=SubmissionType.CODING,
                                        submitted_at=sub_time,
                                        is_passed=True,
                                        details={
                                            "max_score": entry.get("max_score"),
                                            "submission_count": entry.get("submission_count", 1),
                                            "source": "manual_sync",
                                        },
                                    )
                                )
                                synced_coding += 1
            except Exception as e:
                logger.warning(f"Error syncing coding submissions for slug={slug}: {e}")

        # 2. Đồng bộ Game nếu bài tập có yêu cầu game
        if homework.requires_game:
            try:
                # 2.1 Thử lấy danh sách đầy đủ tất cả các Game Session hoàn thành
                game_sessions = await self.quiz_api.get_game_sessions_for_sync(slug)
                if game_sessions is not None:
                    for s in game_sessions:
                        uid = s.get("user_id")
                        if not uid or uid >= 1_000_000:
                            continue

                        # Chỉ lấy những session đạt tiêu chuẩn hoàn thành 100% câu hỏi
                        if not s.get("is_completed", False):
                            continue

                        raw_sub_at = s.get("completed_at")
                        sub_time = to_utc7_naive(raw_sub_at)
                        if not sub_time:
                            logger.warning(
                                f"[SyncFromQuiz] Bỏ qua Game session user_id={uid} (slug='{slug}') "
                                f"do Quiz không có completed_at hợp lệ: {s}"
                            )
                            continue

                        session_id = s.get("session_id")
                        details = {
                            "session_id": session_id,
                            "final_score": s.get("final_score", 0),
                            "gold": s.get("gold", 0),
                            "attempt_count": s.get("attempt_count", 1),
                            "total_questions": s.get("total_questions", 0),
                            "correct_count": s.get("correct_count", 0),
                            "source": "manual_sync",
                        }

                        # Đối soát xem game session này đã có trong Manage chưa
                        existing = self.homework_repo.find_submission_match(
                            homework.id,
                            uid,
                            SubmissionType.GAME,
                            quiz_submission_id=session_id,
                            submitted_at=sub_time,
                        )
                        if existing:
                            # Ghi đè / Cập nhật lại thông tin mới nhất
                            self.homework_repo.update_submission(
                                existing,
                                submitted_at=sub_time,
                                is_passed=True,
                                details=details,
                            )
                            updated_game += 1
                        else:
                            # Thêm mới vào lịch sử nộp bài
                            self.homework_repo.add_submission(
                                HomeworkSubmission(
                                    homework_id=homework.id,
                                    user_id=uid,
                                    submission_type=SubmissionType.GAME,
                                    submitted_at=sub_time,
                                    is_passed=True,
                                    details=details,
                                )
                            )
                            synced_game += 1
                else:
                    # 2.2 Fallback sang leaderboard nếu sessions-for-sync không khả dụng
                    leaderboard = await self.quiz_api.get_game_leaderboard(slug)
                    if leaderboard:
                        for row in leaderboard:
                            uid = row.get("user_id")
                            if not uid or uid >= 1_000_000:
                                continue

                            is_completed = row.get("is_completed", False)
                            total_q = row.get("total_questions", 0)
                            ans_q = row.get("answered_questions", 0)

                            if is_completed and total_q > 0 and ans_q >= total_q:
                                raw_sub_at = row.get("completed_at") or row.get("submitted_at")
                                sub_time = to_utc7_naive(raw_sub_at)
                                if not sub_time:
                                    continue

                                existing = self.homework_repo.find_submission_match(
                                    homework.id,
                                    uid,
                                    SubmissionType.GAME,
                                    submitted_at=sub_time,
                                )
                                if not existing:
                                    self.homework_repo.add_submission(
                                        HomeworkSubmission(
                                            homework_id=homework.id,
                                            user_id=uid,
                                            submission_type=SubmissionType.GAME,
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
                                    synced_game += 1
            except Exception as e:
                logger.warning(f"Error syncing game leaderboard for slug={slug}: {e}")

        logger.info(
            f"✅ [SyncFromQuiz] Hoàn tất đồng bộ bài tập id={homework_id}: "
            f"Coding: +{synced_coding} mới, ~{updated_coding} cập nhật | "
            f"Game: +{synced_game} mới, ~{updated_game} cập nhật"
        )

        return {
            "homework_id": homework.id,
            "title": homework.title,
            "synced_coding_count": synced_coding,
            "updated_coding_count": updated_coding,
            "synced_game_count": synced_game,
            "updated_game_count": updated_game,
            "message": (
                f"Đồng bộ thành công: Coding (+{synced_coding} mới, ~{updated_coding} cập nhật), "
                f"Game (+{synced_game} mới, ~{updated_game} cập nhật)."
            ),
        }
