from datetime import datetime
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field, field_validator

from app.homework.domain.entity import HomeworkSubmission, SubmissionType
from app.homework.infrastructure.repository import HomeworkRepository
from app.utils.datetime import to_utc7_naive


class HomeworkSubmissionWebhookIn(BaseModel):
    """Payload schema nhận từ Quiz Webhook khi có sự kiện nộp bài hoặc hoàn thành game."""

    lesson_slug: str
    user_id: int
    type: SubmissionType
    submitted_at: datetime
    is_passed: bool = True
    
    # Chi tiết bài tập con (dành cho CODING)
    exercise_id: str | None = None
    exercise_title: str | None = None
    submission_id: str | None = None
    attempt_number: int = 1
    score: float | None = None
    original_filename: str | None = None
    
    details: dict[str, Any] = Field(default_factory=dict)

    @field_validator("type", mode="before")
    @classmethod
    def parse_submission_type(cls, v: Any) -> SubmissionType:
        if isinstance(v, SubmissionType):
            return v
        if isinstance(v, str):
            val = v.strip().upper()
            if val in SubmissionType.__members__:
                return SubmissionType[val]
        raise ValueError(f"Invalid submission type: {v}. Must be CODING or GAME")


class RecordHomeworkSubmissionUseCase:
    """Xử lý và lưu vết lịch sử nộp bài (Append-Only) nhận được từ Quiz Webhook."""

    def __init__(self, homework_repo: HomeworkRepository):
        self.homework_repo = homework_repo

    async def execute(self, payload: HomeworkSubmissionWebhookIn) -> dict[str, Any]:
        # 1. Bỏ qua người dùng vãng lai bên ngoài nền tảng (user_id >= 1,000,000)
        if payload.user_id >= 1_000_000:
            logger.info(
                f"[Webhook] Bỏ qua submission của user_id={payload.user_id} (External user)"
            )
            return {
                "status": "ignored",
                "reason": "External user (id >= 1,000,000)",
            }

        # 2. Tìm homework theo lesson_slug
        homework = self.homework_repo.get_by_slug(payload.lesson_slug)
        if not homework or not homework.id:
            logger.warning(
                f"[Webhook] Không tìm thấy bài tập với slug='{payload.lesson_slug}'"
            )
            return {
                "status": "ignored",
                "reason": f"Homework not found for slug '{payload.lesson_slug}'",
            }

        # 3. Chuẩn hóa submitted_at về naive ICT datetime, bỏ qua nếu không hợp lệ
        submitted_at = to_utc7_naive(payload.submitted_at)
        if not submitted_at:
            logger.warning(
                f"[Webhook] Bỏ qua submission user_id={payload.user_id} cho slug='{payload.lesson_slug}' "
                f"do mốc thời gian submitted_at không hợp lệ"
            )
            return {
                "status": "ignored",
                "reason": "Missing or invalid submitted_at timestamp",
            }

        details = dict(payload.details or {})
        sub_id = payload.submission_id or details.get("submission_id")
        if sub_id:
            details["submission_id"] = str(sub_id)
        if payload.original_filename:
            details["original_filename"] = payload.original_filename

        exercise_id = payload.exercise_id or details.get("exercise_id")
        exercise_title = payload.exercise_title or details.get("exercise_title")
        score = payload.score if payload.score is not None else details.get("score")
        attempt_number = payload.attempt_number or details.get("attempt_number", 1)

        # 4. Lưu hoặc cập nhật bản ghi lịch sử vào database (Idempotent Upsert)
        existing = self.homework_repo.find_submission_match(
            homework.id,
            payload.user_id,
            payload.type,
            exercise_id=exercise_id,
            quiz_submission_id=str(sub_id) if sub_id else None,
            submitted_at=submitted_at,
        )
        if existing:
            saved = self.homework_repo.update_submission(
                existing,
                submitted_at=submitted_at,
                is_passed=payload.is_passed,
                exercise_id=exercise_id,
                exercise_title=exercise_title,
                score=float(score) if score is not None else None,
                attempt_number=int(attempt_number) if attempt_number else 1,
                details=details,
            )
            logger.info(
                f"✅ [Webhook] Cập nhật lịch sử bài nộp: id={saved.id}, hw_id={homework.id}, "
                f"user_id={payload.user_id}, type={payload.type}, exercise_id={exercise_id}, is_passed={payload.is_passed}"
            )
            return {
                "status": "updated",
                "submission_id": saved.id,
                "homework_id": homework.id,
                "user_id": payload.user_id,
                "exercise_id": exercise_id,
            }

        if payload.type == SubmissionType.GAME:
            submission = HomeworkSubmission.create_game(
                homework_id=homework.id,
                user_id=payload.user_id,
                submitted_at=submitted_at,
                score=float(score) if score is not None else None,
                attempt_number=int(attempt_number) if attempt_number else 1,
                is_passed=payload.is_passed,
                details=details,
            )
        else:
            final_exercise_id = str(exercise_id) if exercise_id else f"legacy-{homework.id}-{sub_id or payload.user_id}"
            submission = HomeworkSubmission.create_coding(
                homework_id=homework.id,
                user_id=payload.user_id,
                exercise_id=final_exercise_id,
                submitted_at=submitted_at,
                exercise_title=exercise_title,
                score=float(score) if score is not None else None,
                attempt_number=int(attempt_number) if attempt_number else 1,
                is_passed=payload.is_passed,
                details=details,
            )
        saved = self.homework_repo.add_submission(submission)

        logger.info(
            f"✅ [Webhook] Ghi nhận mới lịch sử bài nộp: id={saved.id}, hw_id={homework.id}, "
            f"user_id={payload.user_id}, type={payload.type}, exercise_id={getattr(submission, 'exercise_id', None)}, is_passed={payload.is_passed}"
        )


        return {
            "status": "recorded",
            "submission_id": saved.id,
            "homework_id": homework.id,
            "user_id": payload.user_id,
            "exercise_id": exercise_id,
        }

