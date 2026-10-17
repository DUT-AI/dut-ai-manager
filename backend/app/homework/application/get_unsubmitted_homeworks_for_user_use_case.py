from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)


class GetUnsubmittedHomeworksForUserUseCase:
    """Use case lấy danh sách bài tập chưa nộp của một học viên cụ thể kiểm tra qua database."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
    ):
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo

    async def execute(self, user_id: int) -> list[HomeworkEntity]:
        # 1. Truy vấn bài tập được giao cho user trực tiếp từ Database thông qua SQL JOIN
        assigned_homeworks = self.homework_repo.get_all_assigned_to_user(
            user_id=user_id, deleted=False
        )

        if not assigned_homeworks:
            return []

        # 2. Get user submissions for these homeworks
        hw_ids = [hw.id for hw in assigned_homeworks if hw.id is not None]
        user_submissions = (
            self.homework_submission_repo.get_user_submissions_for_homeworks(
                homework_ids=hw_ids, user_id=user_id
            )
        )

        submissions_by_hw: dict[int, list] = {}
        for sub in user_submissions:
            submissions_by_hw.setdefault(sub.homework_id, []).append(sub)

        # 3. Determine unsubmitted homeworks
        unsubmitted: list[HomeworkEntity] = []
        for hw in assigned_homeworks:
            assert hw.id is not None
            hw_subs = submissions_by_hw.get(hw.id, [])
            if not hw.evaluate_submissions(hw_subs).is_submitted:
                unsubmitted.append(hw)

        return unsubmitted
