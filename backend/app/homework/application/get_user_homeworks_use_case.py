from app.homework.application.dtos import HomeworkResponse
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)
from app.utils.datetime import get_current_utc7_time


class GetUserHomeworksUseCase:
    """Use case lấy danh sách bài tập được giao cho một học viên kèm trạng thái nộp bài DB-First."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
    ):
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo

    async def execute(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[HomeworkResponse], int]:
        # Tối ưu hóa: Truy vấn phân trang trực tiếp từ SQL JOIN giữa homeworks và homework_assignees
        paged_hw, total = self.homework_repo.get_assigned_to_user_paged(
            user_id=user_id,
            page=page,
            page_size=page_size,
        )

        if not paged_hw:
            return [], total

        now = get_current_utc7_time()

        # Query all submissions of user_id for the paged homeworks from database
        paged_hw_ids = [hw.id for hw in paged_hw if hw.id is not None]
        user_submissions = (
            self.homework_submission_repo.get_user_submissions_for_homeworks(
                homework_ids=paged_hw_ids, user_id=user_id
            )
        )

        # Group submissions by homework_id
        submissions_by_hw: dict[int, list] = {}
        for sub in user_submissions:
            submissions_by_hw.setdefault(sub.homework_id, []).append(sub)

        responses: list[HomeworkResponse] = []
        for hw in paged_hw:
            assert hw.id is not None
            hw_subs = submissions_by_hw.get(hw.id, [])
            evaluation = hw.evaluate_submissions(hw_subs, reference_time=now)

            resp = HomeworkResponse(
                id=hw.id,
                title=hw.title,
                deadline=hw.deadline,
                link=hw.link,
                slug=hw.slug,
                requires_coding=hw.requires_coding,
                requires_game=hw.requires_game,
                created_at=hw.created_at,
                updated_at=hw.updated_at,
                created_by=hw.created_by,
                is_submitted=evaluation.is_submitted,
                is_overdue=evaluation.is_overdue,
                has_coding=hw.requires_coding,
                coding_submitted=evaluation.coding_submitted,
                has_game=hw.requires_game,
                game_submitted=evaluation.game_submitted,
                uncompleted_items=evaluation.uncompleted_items,
            )
            responses.append(resp)

        return responses, total
