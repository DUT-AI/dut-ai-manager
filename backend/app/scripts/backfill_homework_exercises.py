"""
One-time backfill CLI script:
Đồng bộ danh mục bài tập con chính thức (`homework_exercises`) và lịch sử bài nộp
cho toàn bộ bài tập đang hoạt động từ Quiz API.

Usage:
    cd backend
    uv run python -m app.scripts.backfill_homework_exercises
    uv run python -m app.scripts.backfill_homework_exercises --exercises-only
"""

import argparse
import asyncio

from loguru import logger
from sqlalchemy.orm import Session

# Register all SQLAlchemy ORM models so cross-module relationships (e.g. UserModel -> MeetingParticipant) resolve cleanly
import app.auth.infrastructure.model  # noqa: F401
import app.billing.infrastructure.model  # noqa: F401
import app.bonus_point.infrastructure.model  # noqa: F401
import app.chatbot.infrastructure.models  # noqa: F401
import app.duty.infrastructure.model  # noqa: F401
import app.expense.infrastructure.model  # noqa: F401
import app.homework.infrastructure.model  # noqa: F401
import app.meeting.infrastructure.model  # noqa: F401
import app.permission_request.infrastructure.model  # noqa: F401
import app.rbac.infrastructure.model  # noqa: F401
import app.reminder.infrastructure.model  # noqa: F401
import app.team.infrastructure.model  # noqa: F401
import app.user.infrastructure.model  # noqa: F401
import app.user.infrastructure.monthly_stats_model  # noqa: F401
import app.violation.infrastructure.model  # noqa: F401
from app.homework.application.backfill_homework_exercises_use_case import (
    BackfillHomeworkExercisesUseCase,
)
from app.homework.application.sync_homework_use_case import (
    SyncHomeworkFromQuizUseCase,
)
from app.homework.infrastructure.homework_exercise_repository import (
    HomeworkExerciseRepository,
)
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.shared.infrastructure.database import engine


async def main(sync_submissions: bool = True) -> None:
    with Session(engine) as session:
        hw_repo = HomeworkRepository(session)
        sub_repo = HomeworkSubmissionRepository(session)
        ex_repo = HomeworkExerciseRepository(session)
        quiz_api = QuizApiClient()

        sync_uc = SyncHomeworkFromQuizUseCase(
            homework_repo=hw_repo,
            homework_submission_repo=sub_repo,
            homework_exercise_repo=ex_repo,
            quiz_api=quiz_api,
        )
        backfill_uc = BackfillHomeworkExercisesUseCase(
            homework_repo=hw_repo,
            sync_homework_uc=sync_uc,
        )

        result = await backfill_uc.execute(sync_submissions=sync_submissions)
        session.commit()

        logger.info(
            f"Backfill hoàn tất: total={result.total_homeworks}, "
            f"succeeded={result.succeeded}, skipped_no_slug={result.skipped_no_slug}, "
            f"failed={result.failed}"
        )
        for item in result.failed_details:
            logger.warning(
                f"  - Failed homework_id={item.homework_id} ('{item.title}'): {item.error}"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Backfill official homework_exercises catalog from Quiz API."
    )
    parser.add_argument(
        "--exercises-only",
        action="store_true",
        help="Chỉ đồng bộ danh mục homework_exercises, không kéo lại submissions.",
    )
    args = parser.parse_args()
    asyncio.run(main(sync_submissions=not args.exercises_only))
