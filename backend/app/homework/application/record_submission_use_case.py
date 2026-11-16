from loguru import logger

from app.homework.application.dtos import (
    HomeworkSubmissionWebhookIn,
    HomeworkWebhookResponse,
)
from app.homework.domain.entity import HomeworkSubmission, SubmissionType
from app.homework.domain.ports import (
    HomeworkRepositoryPort,
    HomeworkSubmissionRepositoryPort,
)
from app.homework.domain.value_objects import (
    CodingSubmissionDetails,
    GameSubmissionDetails,
)


class RecordHomeworkSubmissionUseCase:
    """Xử lý và lưu vết lịch sử nộp bài (Append-Only) nhận được từ Quiz Webhook."""

    def __init__(
        self,
        homework_repo: HomeworkRepositoryPort,
        homework_submission_repo: HomeworkSubmissionRepositoryPort,
    ):
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo

    async def execute(
        self, payload: HomeworkSubmissionWebhookIn
    ) -> HomeworkWebhookResponse:
        # 1. Bỏ qua người dùng vãng lai bên ngoài nền tảng (user_id >= 1,000,000)
        if payload.user_id >= 1_000_000:
            logger.info(
                f"[Webhook] Bỏ qua submission của user_id={payload.user_id} (External user)"
            )
            return HomeworkWebhookResponse(
                status="ignored",
                reason="External user (id >= 1,000,000)",
            )

        # 2. Tìm homework theo lesson_slug
        homework = self.homework_repo.get_by_slug(payload.lesson_slug)
        if not homework or not homework.id:
            logger.warning(
                f"[Webhook] Không tìm thấy bài tập với slug='{payload.lesson_slug}'"
            )
            return HomeworkWebhookResponse(
                status="ignored",
                reason=f"Homework not found for slug '{payload.lesson_slug}'",
            )

        # 3. Chuẩn hóa submitted_at về UTC aware datetime
        submitted_at = payload.submitted_at
        if not submitted_at:
            logger.warning(
                f"[Webhook] Bỏ qua submission user_id={payload.user_id} cho slug='{payload.lesson_slug}' "
                f"do mốc thời gian submitted_at không hợp lệ"
            )
            return HomeworkWebhookResponse(
                status="ignored",
                reason="Missing or invalid submitted_at timestamp",
            )

        raw_details = (
            payload.details.model_dump(exclude_none=True)
            if payload.details and hasattr(payload.details, "model_dump")
            else dict(payload.details or {})
        )
        sub_id = payload.submission_id or raw_details.get("submission_id")
        if sub_id:
            raw_details["submission_id"] = str(sub_id)
        if payload.original_filename:
            raw_details["original_filename"] = payload.original_filename

        exercise_id = payload.exercise_id or raw_details.get("exercise_id")
        exercise_title = payload.exercise_title or raw_details.get("exercise_title")
        score = (
            payload.score
            if payload.score is not None
            else raw_details.get("score") or raw_details.get("final_score")
        )
        attempt_number = (
            payload.attempt_number
            or raw_details.get("attempt_number")
            or raw_details.get("attempt_count", 1)
        )
        raw_details.setdefault("source", "webhook")

        typed_details: CodingSubmissionDetails | GameSubmissionDetails = (
            GameSubmissionDetails(**raw_details)
            if payload.type == SubmissionType.GAME
            else CodingSubmissionDetails(**raw_details)
        )

        # 4. Lưu hoặc cập nhật bản ghi lịch sử vào database (Idempotent Upsert)
        existing = self.homework_submission_repo.find_submission_match(
            homework.id,
            payload.user_id,
            payload.type,
            exercise_id=exercise_id,
            quiz_submission_id=str(sub_id) if sub_id else None,
            submitted_at=submitted_at,
        )
        if existing:
            saved = self.homework_submission_repo.update_submission(
                existing,
                submitted_at=submitted_at,
                is_passed=payload.is_passed,
                exercise_id=exercise_id,
                exercise_title=exercise_title,
                score=float(score) if score is not None else None,
                attempt_number=int(attempt_number) if attempt_number else 1,
                details=typed_details,
            )
            logger.info(
                f"✅ [Webhook] Cập nhật lịch sử bài nộp: id={saved.id}, hw_id={homework.id}, "
                f"user_id={payload.user_id}, type={payload.type}, exercise_id={exercise_id}, is_passed={payload.is_passed}"
            )
            return HomeworkWebhookResponse(
                status="updated",
                submission_id=saved.id,
                homework_id=homework.id,
                user_id=payload.user_id,
                exercise_id=exercise_id,
            )

        if payload.type == SubmissionType.GAME:
            submission = HomeworkSubmission.create_game(
                homework_id=homework.id,
                user_id=payload.user_id,
                submitted_at=submitted_at,
                score=float(score) if score is not None else None,
                attempt_number=int(attempt_number) if attempt_number else 1,
                is_passed=payload.is_passed,
                details=typed_details,
            )
        else:
            final_exercise_id = (
                str(exercise_id)
                if exercise_id
                else f"legacy-{homework.id}-{sub_id or payload.user_id}"
            )
            submission = HomeworkSubmission.create_coding(
                homework_id=homework.id,
                user_id=payload.user_id,
                exercise_id=final_exercise_id,
                submitted_at=submitted_at,
                exercise_title=exercise_title,
                score=float(score) if score is not None else None,
                attempt_number=int(attempt_number) if attempt_number else 1,
                is_passed=payload.is_passed,
                details=typed_details,
            )
        saved = self.homework_submission_repo.add_submission(submission)

        logger.info(
            f"✅ [Webhook] Ghi nhận mới lịch sử bài nộp: id={saved.id}, hw_id={homework.id}, "
            f"user_id={payload.user_id}, type={payload.type}, exercise_id={submission.exercise_id}, is_passed={payload.is_passed}"
        )

        return HomeworkWebhookResponse(
            status="recorded",
            submission_id=saved.id,
            homework_id=homework.id,
            user_id=payload.user_id,
            exercise_id=exercise_id,
        )
