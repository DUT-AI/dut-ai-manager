from datetime import datetime

from app.homework.domain.entity import HomeworkSubmission, SubmissionType
from app.homework.domain.ports import HomeworkSubmissionRepositoryPort
from app.homework.domain.value_objects import (
    CodingSubmissionDetails,
    GameSubmissionDetails,
)


class InMemoryHomeworkSubmissionRepository(HomeworkSubmissionRepositoryPort):
    """Cài đặt In-Memory của HomeworkSubmissionRepositoryPort phục vụ kiểm thử nhanh và độc lập."""

    def __init__(
        self, initial_submissions: list[HomeworkSubmission] | None = None
    ) -> None:
        self._submissions: list[HomeworkSubmission] = []
        self._next_id: int = 1
        if initial_submissions:
            self.add_submissions(initial_submissions)

    def add_submission(self, submission: HomeworkSubmission) -> HomeworkSubmission:
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
        submitted_at: datetime | None = None,
        is_passed: bool | None = None,
        exercise_id: str | None = None,
        exercise_title: str | None = None,
        score: float | None = None,
        attempt_number: int | None = None,
        details: CodingSubmissionDetails | GameSubmissionDetails | None = None,
        external_submission_id: str | None = None,
    ) -> HomeworkSubmission:
        updated = submission.model_copy(
            update={
                "submitted_at": (
                    submitted_at if submitted_at is not None else submission.submitted_at
                ),
                "is_passed": (
                    is_passed if is_passed is not None else submission.is_passed
                ),
                "exercise_id": (
                    exercise_id if exercise_id is not None else submission.exercise_id
                ),
                "external_submission_id": (
                    external_submission_id
                    if external_submission_id is not None
                    else submission.external_submission_id
                ),
                "exercise_title": (
                    exercise_title
                    if exercise_title is not None
                    else submission.exercise_title
                ),
                "score": score if score is not None else submission.score,
                "attempt_number": (
                    attempt_number
                    if attempt_number is not None
                    else submission.attempt_number
                ),
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
        items = [
            s
            for s in self._submissions
            if s.homework_id == homework_id and s.user_id == user_id
        ]
        items.sort(key=lambda x: x.submitted_at, reverse=True)
        return items

    def get_user_submissions_for_homeworks(
        self, homework_ids: list[int], user_id: int
    ) -> list[HomeworkSubmission]:
        hw_set = set(homework_ids)
        items = [
            s
            for s in self._submissions
            if s.homework_id in hw_set and s.user_id == user_id
        ]
        items.sort(key=lambda x: x.submitted_at, reverse=True)
        return items

    def get_all_submissions(self) -> list[HomeworkSubmission]:
        return list(self._submissions)

    def get_submissions_by_homework(
        self, homework_id: int
    ) -> list[HomeworkSubmission]:
        items = [s for s in self._submissions if s.homework_id == homework_id]
        items.sort(key=lambda x: x.submitted_at, reverse=True)
        return items

    def find_submission_match(
        self,
        homework_id: int,
        user_id: int,
        submission_type: SubmissionType,
        exercise_id: str | None = None,
        external_submission_id: str | None = None,
        submitted_at: datetime | None = None,
    ) -> HomeworkSubmission | None:
        if external_submission_id:
            clean_ext_id = str(external_submission_id).strip()
            for s in reversed(self._submissions):
                if (
                    s.homework_id == homework_id
                    and s.user_id == user_id
                    and s.submission_type == submission_type
                    and s.external_submission_id == clean_ext_id
                ):
                    return s
            return None

        if submitted_at:
            for s in reversed(self._submissions):
                if (
                    s.homework_id == homework_id
                    and s.user_id == user_id
                    and s.submission_type == submission_type
                    and s.submitted_at == submitted_at
                ):
                    if (
                        submission_type == SubmissionType.CODING
                        and exercise_id
                        and s.exercise_id != exercise_id
                    ):
                        continue
                    return s

        return None

    def get_submissions_by_exercise(
        self, homework_id: int, exercise_id: str
    ) -> list[HomeworkSubmission]:
        items = [
            s
            for s in self._submissions
            if s.homework_id == homework_id and s.exercise_id == exercise_id
        ]
        items.sort(key=lambda x: x.submitted_at, reverse=True)
        return items

    def get_submitted_exercise_ids(
        self, homework_id: int, user_id: int
    ) -> set[str]:
        return {
            s.exercise_id
            for s in self.get_submissions_by_user(homework_id, user_id)
            if s.exercise_id and s.is_passed
        }
