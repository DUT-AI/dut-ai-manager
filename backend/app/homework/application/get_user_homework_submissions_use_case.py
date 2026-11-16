"""
Get User Homework Submissions Use Case — application layer.
Lấy danh sách lịch sử nộp bài (Audit trail) của học viên cho 1 bài tập.
"""

from app.homework.application.dtos import HomeworkSubmissionDetailResponse
from app.homework.domain.entity import SubmissionType
from app.homework.domain.ports import HomeworkSubmissionRepositoryPort
from app.homework.domain.value_objects import (
    CodingSubmissionDetails,
    GameSubmissionDetails,
)


class GetUserHomeworkSubmissionsUseCase:
    """Lấy danh sách lịch sử tất cả các lần nộp bài (Audit log) của 1 học viên."""

    def __init__(self, homework_submission_repo: HomeworkSubmissionRepositoryPort):
        self.homework_submission_repo = homework_submission_repo

    async def execute(
        self, homework_id: int, user_id: int
    ) -> list[HomeworkSubmissionDetailResponse]:
        submissions = self.homework_submission_repo.get_submissions_by_user(
            homework_id, user_id
        )
        return [
            HomeworkSubmissionDetailResponse(
                id=s.id,
                homework_id=s.homework_id,
                user_id=s.user_id,
                submission_type=s.submission_type,
                exercise_id=s.exercise_id,
                exercise_title=s.exercise_title,
                score=s.score,
                attempt_number=s.attempt_number or 1,
                submitted_at=s.submitted_at,
                is_passed=s.is_passed,
                details=s.details
                or (
                    GameSubmissionDetails()
                    if s.submission_type == SubmissionType.GAME
                    else CodingSubmissionDetails()
                ),
                created_at=s.created_at,
            )
            for s in submissions
            if s.id is not None
        ]
