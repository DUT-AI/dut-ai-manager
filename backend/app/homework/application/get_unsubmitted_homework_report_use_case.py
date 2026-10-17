from app.homework.application.dtos import HomeworkReportResponse
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)
from app.shared.domain.value_objects import UserRef
from app.user.infrastructure.repository import UserRepository


class GetUnsubmittedHomeworkReportUseCase:
    """Use case thống kê tổng hợp số lượng bài tập chưa nộp của toàn bộ học viên đang hoạt động qua DB."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
        user_repo: UserRepository,
    ):
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo
        self.user_repo = user_repo

    async def execute(self) -> list[HomeworkReportResponse]:
        active_users = self.user_repo.get_active_users()
        if not active_users:
            return []

        all_homeworks = self.homework_repo.get_all()
        all_submissions = self.homework_submission_repo.get_all_submissions()

        # Group submissions by (homework_id, user_id)
        subs_map: dict[tuple[int, int], list] = {}
        for sub in all_submissions:
            subs_map.setdefault((sub.homework_id, sub.user_id), []).append(sub)

        # 2. Duyệt qua từng user và đếm số bài chưa nộp
        reports: list[HomeworkReportResponse] = []
        for user in active_users:
            if not user.id:
                continue
            uid = user.id
            unsubmitted_count = 0

            for hw in all_homeworks:
                if not hw.id:
                    continue
                if uid not in (hw.assignee_ids or []):
                    continue

                hw_subs = subs_map.get((hw.id, uid), [])
                if not hw.evaluate_submissions(hw_subs).is_submitted:
                    unsubmitted_count += 1

            reports.append(
                HomeworkReportResponse(
                    user_id=uid,
                    owner=UserRef(
                        id=user.id,
                        name=user.name,
                        email=user.email,
                        avatar_url=user.avatar_url,
                    ),
                    unsubmitted_count=unsubmitted_count,
                )
            )

        # Sắp xếp số bài chưa nộp nhiều nhất lên trước
        reports.sort(key=lambda r: r.unsubmitted_count, reverse=True)
        return reports
