"""
Get User Homework Submissions Use Case — application layer.
Lấy danh sách lịch sử nộp bài (Audit trail) của học viên cho 1 bài tập.
"""

from app.homework.application.dtos import HomeworkSubmissionDetailResponse
from app.homework.infrastructure.repository import HomeworkRepository


class GetUserHomeworkSubmissionsUseCase:
    """Lấy danh sách lịch sử tất cả các lần nộp bài (Audit log) của 1 học viên."""

    def __init__(self, homework_repo: HomeworkRepository):
        self.homework_repo = homework_repo

    async def execute(
        self, homework_id: int, user_id: int
    ) -> list[HomeworkSubmissionDetailResponse]:
        submissions = self.homework_repo.get_submissions_by_user(homework_id, user_id)
        return [
            HomeworkSubmissionDetailResponse(
                id=s.id,
                homework_id=s.homework_id,
                user_id=s.user_id,
                submission_type=s.submission_type,
                submitted_at=s.submitted_at,
                is_passed=s.is_passed,
                details=s.details or {},
                created_at=getattr(s, "created_at", None),
            )
            for s in submissions
            if s.id is not None
        ]
