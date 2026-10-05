from datetime import datetime
from typing import Any

from loguru import logger
from pydantic import BaseModel, field_validator

from app.homework.domain.entity import HomeworkSubmission, SubmissionType
from app.homework.infrastructure.repository import HomeworkRepository
from app.utils.datetime import get_current_utc7_time, to_utc7_naive


class HomeworkSubmissionWebhookIn(BaseModel):
    """Payload schema nhận từ Quiz Webhook khi có sự kiện nộp bài hoặc hoàn thành game."""

    lesson_slug: str
    user_id: int
    type: SubmissionType
    submitted_at: datetime | None = None
    is_passed: bool = True
    details: dict[str, Any] | None = None

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

        # 3. Chuẩn hóa submitted_at về naive ICT datetime
        submitted_at = to_utc7_naive(payload.submitted_at) or get_current_utc7_time()

        # 4. Lưu bản ghi lịch sử vào database
        submission = HomeworkSubmission(
            homework_id=homework.id,
            user_id=payload.user_id,
            submission_type=payload.type,
            submitted_at=submitted_at,
            is_passed=payload.is_passed,
            details=payload.details or {},
        )
        saved = self.homework_repo.add_submission(submission)

        logger.info(
            f"✅ [Webhook] Ghi nhận lịch sử bài nộp: id={saved.id}, hw_id={homework.id}, "
            f"user_id={payload.user_id}, type={payload.type}, is_passed={payload.is_passed}"
        )

        return {
            "status": "recorded",
            "submission_id": saved.id,
            "homework_id": homework.id,
            "user_id": payload.user_id,
        }
