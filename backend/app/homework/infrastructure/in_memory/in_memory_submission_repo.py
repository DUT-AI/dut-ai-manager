from datetime import datetime

from app.homework.domain.entity import HomeworkSubmission, SubmissionType
from app.homework.domain.ports import HomeworkSubmissionRepositoryPort
from app.homework.domain.value_objects import (
    CodingSubmissionDetails,
    GameSubmissionDetails,
)


class InMemoryHomeworkSubmissionRepository(HomeworkSubmissionRepositoryPort):
    """Cài đặt In-Memory của HomeworkSubmissionRepositoryPort phục vụ kiểm thử nhanh và độc lập."""

    def __init__(self, initial_submissions: list[HomeworkSubmission] | None = None) -> None:
        self._submissions: list[HomeworkSubmission] = []
        self._next_id: int = 1
        if initial_submissions:
            self.add_submissions(initial_submissions)

    def add_submission(
        self, submission: HomeworkSubmission
    ) -> HomeworkSubmission:
        if submission.id is None:
            submission = submission.model_copy(update={"id": self._next_id})
            self._next_id += 1
        self._submissions.append(submission)
        return submission

    def add(self, submission: HomeworkSubmission) -> HomeworkSubmission:
        """Alias cho add_submission phục vụ test fixtures ngắn gọn."""
        return self.add_submission(submission)

    def add_submissions(
        self, submissions: list[HomeworkSubmission]
    ) -> list[HomeworkSubmission]:
        """Thêm hàng loạt bài nộp phục vụ seeding test data."""
        return [self.add_submission(s) for s in submissions]

    def clear(self) -> None:
        """Xóa toàn bộ bài nộp trong RAM."""
        self._submissions.clear()
        self._next_id = 1

    def count(self) -> int:
        return len(self._submissions)

    def update_submission(
        self,
        submission: HomeworkSubmission,
        submitted_at: datetime,
        is_passed: bool,
        exercise_id: str | None = None,
        exercise_title: str | None = None,
        score: float | None = None,
        attempt_number: int = 1,
        details: CodingSubmissionDetails | GameSubmissionDetails | None = None,
    ) -> HomeworkSubmission:
        updated = submission.model_copy(
            update={
                "submitted_at": submitted_at,
                "is_passed": is_passed,
                "exercise_id": exercise_id if exercise_id is not None else submission.exercise_id,
                "exercise_title": exercise_title if exercise_title is not None else submission.exercise_title,
                "score": score if score is not None else submission.score,
                "attempt_number": attempt_number,
                "details": details if details is not None else submission.details,
            }
        )
        for idx, sub in enumerate(self._submissions):
            if sub.id == submission.id:
                self._submissions[idx] = updated
                break
        return updated

    def get_submissions_by_user(
        self, homework_id: int, user_id: int
    ) -> list[HomeworkSubmission]:
        return [
            s for s in self._submissions
            if s.homework_id == homework_id and s.user_id == user_id
        ]

    def get_user_submissions_for_homeworks(
        self, homework_ids: list[int], user_id: int
    ) -> dict[int, list[HomeworkSubmission]]:
        res: dict[int, list[HomeworkSubmission]] = {hid: [] for hid in homework_ids}
        for s in self._submissions:
            if s.homework_id in res and s.user_id == user_id:
                res[s.homework_id].append(s)
        return res

    def get_all_submissions(self) -> list[HomeworkSubmission]:
        return list(self._submissions)

    def get_submissions_by_homework(
        self, homework_id: int
    ) -> list[HomeworkSubmission]:
        return [s for s in self._submissions if s.homework_id == homework_id]

    def find_submission_match(
        self,
        homework_id: int,
        user_id: int,
        submission_type: SubmissionType,
        exercise_id: str | None = None,
        quiz_submission_id: str | None = None,
        submitted_at: datetime | None = None,
    ) -> HomeworkSubmission | None:
        for s in reversed(self._submissions):
            if s.homework_id != homework_id or s.user_id != user_id:
                continue
            if s.submission_type != submission_type:
                continue
            if exercise_id and s.exercise_id == exercise_id:
                return s
            if quiz_submission_id and hasattr(s.details, "submission_id"):
                if s.details.submission_id == quiz_submission_id:
                    return s
            if submitted_at and s.submitted_at == submitted_at:
                return s
        return None

    def get_submissions_by_exercise(
        self, homework_id: int, exercise_id: str
    ) -> list[HomeworkSubmission]:
        return [
            s for s in self._submissions
            if s.homework_id == homework_id and s.exercise_id == exercise_id
        ]

    def get_submitted_exercise_ids(
        self, homework_id: int, user_id: int
    ) -> set[str]:
        return {
            s.exercise_id for s in self.get_submissions_by_user(homework_id, user_id)
            if s.exercise_id and s.is_passed
        }

    def get_required_exercise_ids_map(
        self, homework_ids: list[int]
    ) -> dict[int, set[str]]:
        res: dict[int, set[str]] = {hid: set() for hid in homework_ids}
        for s in self._submissions:
            if s.homework_id in res and s.exercise_id:
                res[s.homework_id].add(s.exercise_id)
        return res
