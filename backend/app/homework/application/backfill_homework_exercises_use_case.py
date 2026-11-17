from loguru import logger

from app.homework.application.dtos import (
    BackfillFailedItem,
    BackfillHomeworkExercisesResult,
)
from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.application.sync_homework_use_case import (
    SyncHomeworkFromQuizUseCase,
)
from app.homework.domain.ports import HomeworkRepositoryPort


class BackfillHomeworkExercisesUseCase:
    """
    Use case chuẩn hóa dữ liệu một lần (Admin/CLI):
    Duyệt toàn bộ bài tập hiện hành và đồng bộ danh mục homework_exercises chính thức
    (tùy chọn đồng bộ kèm submissions) từ Quiz API theo chế độ fail-safe từng bài.
    """

    def __init__(
        self,
        homework_repo: HomeworkRepositoryPort,
        sync_homework_uc: SyncHomeworkFromQuizUseCase,
    ):
        self.homework_repo = homework_repo
        self.sync_homework_uc = sync_homework_uc

    async def execute(
        self, sync_submissions: bool = True
    ) -> BackfillHomeworkExercisesResult:
        all_homeworks = self.homework_repo.get_all(limit=1000)

        succeeded = 0
        skipped_no_slug = 0
        failed_details: list[BackfillFailedItem] = []

        for hw in all_homeworks:
            if not hw.id:
                continue
            slug = QuizSubmissionHelper.extract_slug_from_entity(hw)
            if not slug:
                skipped_no_slug += 1
                continue
            try:
                await self.sync_homework_uc.execute(
                    hw.id, sync_submissions=sync_submissions
                )
                succeeded += 1
            except Exception as exc:
                logger.warning(
                    f"[BackfillExercises] Lỗi đồng bộ homework_id={hw.id} ('{hw.title}'): {exc}"
                )
                failed_details.append(
                    BackfillFailedItem(
                        homework_id=hw.id,
                        title=hw.title,
                        error=str(exc),
                    )
                )

        return BackfillHomeworkExercisesResult(
            total_homeworks=len(all_homeworks),
            succeeded=succeeded,
            skipped_no_slug=skipped_no_slug,
            failed=len(failed_details),
            failed_details=failed_details,
        )
