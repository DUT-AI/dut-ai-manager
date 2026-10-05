from typing import Any

from loguru import logger

from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.domain.entity import HomeworkSubmission, SubmissionType
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.homework.infrastructure.repository import HomeworkRepository
from app.shared.application.response import BadRequestException
from app.utils.datetime import get_current_utc7_time


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
        synced_game = 0

        # 1. Đồng bộ Coding nếu bài tập có yêu cầu coding
        if homework.requires_coding:
            coding_map = await QuizSubmissionHelper.get_coding_completed_map(
                self.quiz_api, slug
            )
            if coding_map:
                for uid, entry in coding_map.items():
                    if uid >= 1_000_000:
                        continue  # Bỏ qua user ngoài platform

                    # Kiểm tra xem user này đã có bản ghi nộp coding chưa
                    has_sub = self.homework_repo.has_valid_submission(
                        homework.id, uid, SubmissionType.CODING, now
                    )
                    if not has_sub:
                        self.homework_repo.add_submission(
                            HomeworkSubmission(
                                homework_id=homework.id,
                                user_id=uid,
                                submission_type=SubmissionType.CODING,
                                submitted_at=now,
                                is_passed=True,
                                details={
                                    "max_score": entry.get("max_score"),
                                    "submission_count": entry.get("submission_count", 1),
                                    "source": "manual_sync",
                                },
                            )
                        )
                        synced_coding += 1

        # 2. Đồng bộ Game nếu bài tập có yêu cầu game
        if homework.requires_game:
            try:
                leaderboard = await self.quiz_api.get_game_leaderboard(slug)
                if leaderboard:
                    for row in leaderboard:
                        uid = row.get("user_id")
                        if not uid or uid >= 1_000_000:
                            continue

                        # Kiểm tra tiêu chuẩn: is_completed và đúng 100% câu hỏi
                        is_completed = row.get("is_completed", False)
                        total_q = row.get("total_questions", 0)
                        ans_q = row.get("answered_questions", 0)

                        if is_completed and total_q > 0 and ans_q >= total_q:
                            has_sub = self.homework_repo.has_valid_submission(
                                homework.id, uid, SubmissionType.GAME, now
                            )
                            if not has_sub:
                                self.homework_repo.add_submission(
                                    HomeworkSubmission(
                                        homework_id=homework.id,
                                        user_id=uid,
                                        submission_type=SubmissionType.GAME,
                                        submitted_at=now,
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
            f"+{synced_coding} coding, +{synced_game} game"
        )

        return {
            "homework_id": homework.id,
            "title": homework.title,
            "synced_coding_count": synced_coding,
            "synced_game_count": synced_game,
            "message": f"Đồng bộ thành công: thêm mới {synced_coding} bài nộp coding và {synced_game} lượt game.",
        }
